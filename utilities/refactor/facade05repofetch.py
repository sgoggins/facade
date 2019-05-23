#!/usr/bin/env python3

# Copyright 2016-2018 Brian Warner
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier:	Apache-2.0

# Git repo maintenance
#
# This script is responsible for cloning new repos and keeping existing repos up
# to date. It can be run as often as you want (and will detect when it's
# already running, so as not to spawn parallel processes), but once or twice per
# day should be more than sufficient. Each time it runs, it updates the repo
# and checks for any parents of HEAD that aren't already accounted for in the
# repos. It also rebuilds analysis data, checks any changed affiliations and
# aliases, and caches data for display.

def git_repo_initialize():

# Select any new git repos so we can set up their locations and git clone

	update_status('Fetching new repos')
	log_activity('Info','Fetching new repos')

	query = "SELECT id,projects_id,git FROM repos WHERE status LIKE 'New%'";
	cursor.execute(query)

	new_repos = list(cursor)

	for row in new_repos:
		print(row["git"])
		update_repo_log(row['id'],'Cloning')

		git = html.unescape(row["git"])

		# Strip protocol from remote URL, set a unique path on the filesystem
		if git.find('://',0) > 0:
			repo_relative_path = git[git.find('://',0)+3:][:git[git.find('://',0)+3:].rfind('/',0)+1]
		else:
			repo_relative_path = git[:git.rfind('/',0)+1]

		# Get the full path to the directory where we'll clone the repo
		repo_path = ('%s%s/%s' %
			(repo_base_directory,row["projects_id"],repo_relative_path))

		# Get the name of repo
		repo_name = git[git.rfind('/',0)+1:]
		if repo_name.find('.git',0) > -1:
			repo_name = repo_name[:repo_name.find('.git',0)]

		# Check if there will be a storage path collision
		query = ("SELECT NULL FROM repos WHERE CONCAT(projects_id,'/',path,name) = %s")
		cursor.execute(query, ('{}/{}{}'.format(row["projects_id"], repo_relative_path, repo_name), ))
		db.commit()

		# If there is a collision, append a slug to repo_name to yield a unique path
		if cursor.rowcount:

			slug = 1
			is_collision = True
			while is_collision:

				if os.path.isdir('%s%s-%s' % (repo_path,repo_name,slug)):
					slug += 1
				else:
					is_collision = False

			repo_name = '%s-%s' % (repo_name,slug)

			log_activity('Verbose','Identical repo detected, storing %s in %s' %
				(git,repo_name))

		# Create the prerequisite directories
		return_code = subprocess.Popen(['mkdir -p %s' %repo_path],shell=True).wait()

		# Make sure it's ok to proceed
		if return_code != 0:
			print("COULD NOT CREATE REPO DIRECTORY")

			update_repo_log(row['id'],'Failed (mkdir)')
			update_status('Failed (mkdir %s)' % repo_path)
			log_activity('Error','Could not create repo directory: %s' %
				repo_path)

			sys.exit("Could not create git repo's prerequisite directories. "
				" Do you have write access?")

		update_repo_log(row['id'],'New (cloning)')

		query = ("UPDATE repos SET status='New (Initializing)', path=%s, "
			"name=%s WHERE id=%s")

		cursor.execute(query, (repo_relative_path,repo_name,row["id"]))
		db.commit()

		log_activity('Verbose','Cloning: %s' % git)

		cmd = "git -C %s clone '%s' %s" % (repo_path,git,repo_name)
		return_code = subprocess.Popen([cmd], shell=True).wait()

		if (return_code == 0):
			# If cloning succeeded, repo is ready for analysis
			# Mark the entire project for an update, so that under normal
			# circumstances caches are rebuilt only once per waiting period.

			update_project_status = ("UPDATE repos SET status='Update' WHERE "
				"projects_id=%s AND status != 'Empty'")
			cursor.execute(update_project_status, (row['projects_id'], ))
			db.commit()

			# Since we just cloned the new repo, set it straight to analyze.
			query = ("UPDATE repos SET status='Analyze',path=%s, name=%s "
				"WHERE id=%s and status != 'Empty'")

			cursor.execute(query, (repo_relative_path,repo_name,row["id"]))
			db.commit()

			update_repo_log(row['id'],'Up-to-date')
			log_activity('Info','Cloned %s' % git)

		else:
			# If cloning failed, log it and set the status back to new
			update_repo_log(row['id'],'Failed (%s)' % return_code)

			query = ("UPDATE repos SET status='New (failed)' WHERE id=%s")

			cursor.execute(query, (row['id'], ))
			db.commit()

			log_activity('Error','Could not clone %s' % git)

	log_activity('Info', 'Fetching new repos (complete)')

	
def check_for_repo_updates():

# Check the last time a repo was updated and if it has been longer than the
# update_frequency, mark its project for updating during the next analysis.

	update_status('Checking if any repos need to update')
	log_activity('Info','Checking repos to update')

	update_frequency = get_setting('update_frequency')

	get_initialized_repos = ("SELECT id FROM repos WHERE status NOT LIKE 'New%' "
		"AND status != 'Delete' "
		"AND status != 'Analyze' AND status != 'Empty'")
	cursor.execute(get_initialized_repos)
	repos = list(cursor)

	for repo in repos:

		# Figure out which repos have been updated within the waiting period

		get_last_update = ("SELECT NULL FROM repos_fetch_log WHERE "
			"repos_id=%s AND status='Up-to-date' AND "
			"date >= CURRENT_TIMESTAMP(6) - INTERVAL %s HOUR ")

		cursor.execute(get_last_update, (repo['id'], update_frequency))

		# If the repo has not been updated within the waiting period, mark it.
		# Also mark any other repos in the project, so we only recache the
		# project once per waiting period.

		if cursor.rowcount == 0:
			mark_repo = ("UPDATE repos r JOIN projects p ON p.id = r.projects_id "
				"SET status='Update' WHERE "
				"r.id=%s and r.status != 'Empty'")
			cursor.execute(mark_repo, (repo['id'], ))
			db.commit()

	# Mark the entire project for an update, so that under normal
	# circumstances caches are rebuilt only once per waiting period.

	update_project_status = ("UPDATE repos r LEFT JOIN repos s ON r.projects_id=s.projects_id "
		"SET r.status='Update' WHERE s.status='Update' AND "
		"r.status != 'Analyze' AND r.status != 'Empty'")
	cursor.execute(update_project_status)
	db.commit()

	log_activity('Info','Checking repos to update (complete)')

def force_repo_updates():

# Set the status of all non-new repos to "Update".

	update_status('Forcing all non-new repos to update')
	log_activity('Info','Forcing repos to update')

	get_repo_ids = ("UPDATE repos SET status='Update' WHERE status "
		"NOT LIKE 'New%' AND STATUS!='Delete' AND STATUS !='Empty'")
	cursor.execute(get_repo_ids)
	db.commit()

	log_activity('Info','Forcing repos to update (complete)')

def force_repo_analysis():

# Set the status of all non-new repos to "Analyze".

	update_status('Forcing all non-new repos to be analyzed')
	log_activity('Info','Forcing repos to be analyzed')

	set_to_analyze = ("UPDATE repos SET status='Analyze' WHERE status "
		"NOT LIKE 'New%' AND STATUS!='Delete' AND STATUS != 'Empty'")
	cursor.execute(set_to_analyze)
	db.commit()

	log_activity('Info','Forcing repos to be analyzed (complete)')

def git_repo_updates():

# Update existing repos

	update_status('Updating repos')
	log_activity('Info','Updating existing repos')

	repo_base_directory = get_setting('repo_directory')

	query = ("SELECT id,projects_id,git,name,path FROM repos WHERE "
		"status='Update'");
	cursor.execute(query)

	existing_repos = list(cursor)

	for row in existing_repos:

		log_activity('Verbose','Attempting to update %s' % row['git'])
		update_repo_log(row['id'],'Updating')

		attempt = 0

		# Try two times. If it fails the first time, reset and clean the git repo,
		# as somebody may have done a rebase. No work is being done in the local
		# repo, so there shouldn't be legit local changes to worry about.

		while attempt < 2:

			cmd = ("git -C %s%s/%s%s pull"
				% (repo_base_directory,row['projects_id'],row['path'],row['name']))

			return_code = subprocess.Popen([cmd],shell=True).wait()

			# If the attempt succeeded, then don't try any further fixes. If
			# the attempt to fix things failed, give up and try next time.
			if return_code == 0 or attempt == 1:
				break

			elif attempt == 0:

				log_activity('Verbose','git pull failed, attempting reset and '
					'clean for %s' % row['git'])

				cmd_reset = ("git -C %s%s/%s%s reset --hard origin/master"
					% (repo_base_directory,row['projects_id'],row['path'],row['name']))

				return_code_reset = subprocess.Popen([cmd_reset],shell=True).wait()

				cmd_clean = ("git -C %s%s/%s%s clean -df"
					% (repo_base_directory,row['projects_id'],row['path'],row['name']))

				return_code_clean = subprocess.Popen([cmd_clean],shell=True).wait()

			attempt += 1

		if return_code == 0:

			set_to_analyze = "UPDATE repos SET status='Analyze' WHERE id=%s"
			cursor.execute(set_to_analyze, (row['id'], ))
			db.commit()

			update_repo_log(row['id'],'Up-to-date')
			log_activity('Verbose','Updated %s' % row["git"])

		else:
			update_repo_log(row['id'],'Failed (%s)' % return_code)
			log_activity('Error','Could not update %s' % row["git"])

	log_activity('Info','Updating existing repos (complete)')