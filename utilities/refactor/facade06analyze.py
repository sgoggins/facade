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


def analysis():

# Run the analysis by looping over all active repos. For each repo, we retrieve
# the list of commits which lead to HEAD. If any are missing from the database,
# they are filled in. Then we check to see if any commits in the database are
# not in the list of parents, and prune them out.
#
# We also keep track of the last commit to be processed, so that if the analysis
# is interrupted (possibly leading to partial data in the database for the
# commit being analyzed at the time) we can recover.

### Local helper functions ###

	def update_analysis_log(repos_id,status):

	# Log a repo's analysis status

		log_message = ("INSERT INTO analysis_log (repos_id,status) "
			"VALUES (%s,%s)")

		cursor.execute(log_message, (repos_id,status))
		db.commit()

### The real function starts here ###

	update_status('Running analysis')
	log_activity('Info','Beginning analysis')

	start_date = get_setting('start_date')

	repo_list = "SELECT id,projects_id,path,name FROM repos WHERE status='Analyze'"
	cursor.execute(repo_list)
	repos = list(cursor)

	for repo in repos:

		update_analysis_log(repo['id'],'Beginning analysis')
		log_activity('Verbose','Analyzing repo: %s (%s)' % (repo['id'],repo['name']))

		# First we check to see if the previous analysis didn't complete

		get_status = ("SELECT working_commit FROM working_commits WHERE repos_id=%s")

		cursor.execute(get_status, (repo['id'], ))
		working_commits = list(cursor)
		#cursor.fetchone()['working_commit']

		# If there's a commit still there, the previous run was interrupted and
		# the commit data may be incomplete. It should be trimmed, just in case.
		for commit in working_commits:
			trim_commit(repo['id'],commit['working_commit'])

			# Remove the working commit.
			remove_commit = ("DELETE FROM working_commits "
				"WHERE repos_id = %s AND working_commit = %s")
			cursor.execute(remove_commit, (repo['id'],commit['working_commit']))
			db.commit()

			log_activity('Debug','Removed working commit: %s' % commit['working_commit'])

		# Start the main analysis

		update_analysis_log(repo['id'],'Collecting data')

		repo_loc = ('%s%s/%s%s/.git' % (repo_base_directory,
			repo["projects_id"], repo["path"],
			repo["name"]))
		# Grab the parents of HEAD

		parents = subprocess.Popen(["git --git-dir %s log --ignore-missing "
			"--pretty=format:'%%H' --since=%s" % (repo_loc,start_date)],
			stdout=subprocess.PIPE, shell=True)

		parent_commits = set(parents.stdout.read().decode("utf-8",errors="ignore").split(os.linesep))

		# If there are no commits in the range, we still get a blank entry in
		# the set. Remove it, as it messes with the calculations

		if '' in parent_commits:
			parent_commits.remove('')

		# Grab the existing commits from the database

		existing_commits = set()

		find_existing = ("SELECT DISTINCT commit FROM analysis_data WHERE repos_id=%s")

		cursor.execute(find_existing, (repo['id'], ))

		for commit in list(cursor):
			existing_commits.add(commit['commit'])

		# Find missing commits and add them

		missing_commits = parent_commits - existing_commits

		log_activity('Debug','Commits missing from repo %s: %s' %
			(repo['id'],len(missing_commits)))

		if multithreaded:

			from multiprocessing import Pool

			pool = Pool()

			for commit in missing_commits:

				result =pool.apply_async(analyze_commit,(repo['id'],repo_loc,commit))

			pool.close()
			pool.join()

		else:
			for commit in missing_commits:
				analyze_commit(repo['id'],repo_loc,commit)

		update_analysis_log(repo['id'],'Data collection complete')

		update_analysis_log(repo['id'],'Beginning to trim commits')

		# Find commits which are out of the analysis range

		trimmed_commits = existing_commits - parent_commits

		log_activity('Debug','Commits to be trimmed from repo %s: %s' %
			(repo['id'],len(trimmed_commits)))

		for commit in trimmed_commits:

			trim_commit(repo['id'],commit)

		set_complete = "UPDATE repos SET status='Complete' WHERE id=%s and status != 'Empty'"

		cursor.execute(set_complete, (repo['id'], ))

		update_analysis_log(repo['id'],'Commit trimming complete')

		update_analysis_log(repo['id'],'Complete')

	log_activity('Info','Running analysis (complete)')