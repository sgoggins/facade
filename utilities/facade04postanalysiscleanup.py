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
import sys
import platform
import imp
import time
import datetime
import html.parser
import subprocess
import os
import getopt
import xlsxwriter
import configparser
if platform.python_implementation() == 'PyPy':
	import pymysql
else:
	import MySQLdb

def git_repo_cleanup(cfg):

# Clean up any git repos that are pending deletion

	cfg.update_status('Purging deleted repos')
	cfg.log_activity('Info','Processing deletions')

	repo_base_directory = cfg.get_setting('repo_directory')

	query = "SELECT id,projects_id,path,name FROM repos WHERE status='Delete'"
	cfg.cursor.execute(query)

	delete_repos = list(cfg.cursor)

	for row in delete_repos:

		# Remove the files on disk

		cmd = ("rm -rf %s%s/%s%s"
			% (repo_base_directory,row['projects_id'],row['path'],row['name']))

		return_code = subprocess.Popen([cmd],shell=True).wait()

		# Remove the analysis data

		remove_analysis_data = "DELETE FROM analysis_data WHERE repos_id=%s"
		cfg.cursor.execute(remove_analysis_data, (row['id'], ))

		optimize_table = "OPTIMIZE TABLE analysis_data"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		# Remove cached repo data

		remove_repo_weekly_cache = "DELETE FROM repo_weekly_cache WHERE repos_id=%s"
		cfg.cursor.execute(remove_repo_weekly_cache, (row['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE repo_weekly_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		remove_repo_monthly_cache = "DELETE FROM repo_monthly_cache WHERE repos_id=%s"
		cfg.cursor.execute(remove_repo_monthly_cache, (row['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE repo_monthly_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		remove_repo_annual_cache = "DELETE FROM repo_annual_cache WHERE repos_id=%s"
		cfg.cursor.execute(remove_repo_annual_cache, (row['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE repo_annual_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		# Set project to be recached if just removing a repo

		set_project_recache = ("UPDATE projects SET recache=TRUE "
			"WHERE id=%s")
		cfg.cursor.execute(set_project_recache,(row['projects_id'], ))
		cfg.db.commit()

		# Remove the entry from the repos table

		query = "DELETE FROM repos WHERE id=%s"
		cfg.cursor.execute(query, (row['id'], ))
		cfg.db.commit()

		log_activity('Verbose','Deleted repo %s' % row['id'])

		cleanup = '%s/%s%s' % (row['projects_id'],row['path'],row['name'])

		# Remove any working commits

		remove_working_commits = "DELETE FROM working_commits WHERE repos_id=%s"
		cfg.cursor.execute(remove_working_commits, (row['id'], ))
		cfg.db.commit()

		# Remove the repo from the logs

		remove_logs = ("DELETE FROM repos_fetch_log WHERE repos_id = %s")

		cfg.cursor.execute(remove_logs, (row['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE repos_fetch_log"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		# Attempt to cleanup any empty parent directories

		while (cleanup.find('/',0) > 0):
			cleanup = cleanup[:cleanup.rfind('/',0)]

			cmd = "rmdir %s%s" % (repo_base_directory,cleanup)
			subprocess.Popen([cmd],shell=True).wait()
			log_activity('Verbose','Attempted %s' % cmd)

		update_repo_log(row['id'],'Deleted')

	# Clean up deleted projects

	get_deleted_projects = "SELECT id FROM projects WHERE name='(Queued for removal)'"
	cfg.cursor.execute(get_deleted_projects)

	deleted_projects = list(cfg.cursor)

	for project in deleted_projects:

		# Remove cached data for projects which were marked for deletion

		clear_annual_cache = ("DELETE FROM project_annual_cache WHERE "
			"projects_id=%s")
		cfg.cursor.execute(clear_annual_cache, (project['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE project_annual_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		clear_monthly_cache = ("DELETE FROM project_monthly_cache WHERE "
			"projects_id=%s")
		cfg.cursor.execute(clear_monthly_cache, (project['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE project_monthly_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		clear_weekly_cache = ("DELETE FROM project_weekly_cache WHERE "
			"projects_id=%s")
		cfg.cursor.execute(clear_weekly_cache, (project['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE project_weekly_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		clear_unknown_cache = ("DELETE FROM unknown_cache WHERE "
			"projects_id=%s")
		cfg.cursor.execute(clear_unknown_cache, (project['id'], ))
		cfg.db.commit()

		optimize_table = "OPTIMIZE TABLE project_weekly_cache"
		cfg.cursor.execute(optimize_table)
		cfg.db.commit()

		# Remove any projects which were also marked for deletion

		remove_project = "DELETE FROM projects WHERE id=%s"
		cfg.cursor.execute(remove_project, (project['id'], ))
		cfg.db.commit()

	cfg.log_activity('Info','Processing deletions (complete)')