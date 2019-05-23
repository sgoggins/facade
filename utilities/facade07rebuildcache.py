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
from facade02utilitymethods import update_repo_log, trim_commit, store_working_author, trim_author
if platform.python_implementation() == 'PyPy':
	import pymysql
else:
	import MySQLdb

def nuke_affiliations(cfg):

# Delete all stored affiliations in the database. Normally when you
# add/remove/change affiliation data via the web UI, any potentially affected
# records will be deleted and then rebuilt on the next run. However, if you
# manually add affiliation records via the database or import them by some other
# means, there's no elegant way to discover which affiliations are affected. So
# this is the scorched earth way: remove them all to force a total rebuild.
# Brutal but effective.

	cfg.log_activity('Info','Nuking affiliations')

	nuke = ("UPDATE analysis_data SET author_affiliation = NULL, "
			"committer_affiliation = NULL")

	cfg.cursor.execute(nuke)
	cfg.db.commit()

	cfg.log_activity('Info','Nuking affiliations (complete)')

def fill_empty_affiliations(cfg):

# When a record is added, it has no affiliation data. Also, when an affiliation
# mapping is changed via the UI, affiliation data will be set to NULL. This
# function finds any records with NULL affiliation data and fills them.

### Local helper functions ###

	def update_affiliation(email_type,email,affiliation,start_date):

		update = ("UPDATE analysis_data "
			"SET %s_affiliation = %%s "
			"WHERE %s_email = %%s "
			"AND %s_affiliation IS NULL "
			"AND %s_date >= %%s" %
			(email_type, email_type, email_type, email_type))

		cfg.cursor.execute(update, (affiliation, email, start_date))
		cfg.db.commit()

	def discover_null_affiliations(attribution,email):

	# Try a bunch of ways to match emails to attributions in the database. First it
	# tries to match exactly. If that doesn't work, it tries to match by domain. If
	# domain doesn't work, it strips subdomains from the email and tries again.

		# First we see if there's an exact match. This will also catch malformed or
		# intentionally mangled emails (e.g. "developer at domain.com") that have
		# been added as an affiliation rather than an alias.

		find_exact_match = ("SELECT affiliation,start_date "
			"FROM affiliations "
			"WHERE domain = %s "
			"AND active = TRUE "
			"ORDER BY start_date DESC")

		cfg.cursor_people.execute(find_exact_match, (email, ))
		cfg.db_people.commit()

		matches = list(cfg.cursor_people)

		if not matches and email.find('@') < 0:

			# It's not a properly formatted email, leave it NULL and log it.

			cfg.log_activity('Info','Unmatchable email: %s' % email)

			return

		if not matches:

			# Now we go for a domain-level match. Try for an exact match.

			domain = email[email.find('@')+1:]

			find_exact_domain = ("SELECT affiliation,start_date "
				"FROM affiliations "
				"WHERE domain= %s "
				"AND active = TRUE "
				"ORDER BY start_date DESC")

			cfg.cursor_people.execute(find_exact_domain, (domain, ))
			cfg.db_people.commit()

			matches = list(cfg.cursor_people)

		if not matches:

			# Then try stripping any subdomains.

			find_domain = ("SELECT affiliation,start_date "
				"FROM affiliations "
				"WHERE domain = %s "
				"AND active = TRUE "
				"ORDER BY start_date DESC")

			cfg.cursor_people.execute(find_domain, (domain[domain.rfind('.',0,domain.rfind('.',0))+1:], ))
			cfg.db_people.commit()

			matches = list(cfg.cursor_people)

		if not matches:

			# One last check to see if it's an unmatched academic domain.

			if domain[-4:] in '.edu':
				matches.append({'affiliation':'(Academic)','start_date':'1970-01-01'})

		# Done looking. Now we process any matches that were found.

		if matches:

			cfg.log_activity('Debug','Found domain match for %s' % email)

			for match in matches:
				update = ("UPDATE analysis_data "
					"SET %s_affiliation = %%s "
					"WHERE %s_email = %%s "
					"AND %s_affiliation IS NULL "
					"AND %s_date >= %%s" %
					(attribution, attribution, attribution, attribution))

				cfg.cursor.execute(update, (match['affiliation'], email, match['start_date']))
				cfg.db.commit()

	def discover_alias(email):

	# Match aliases with their canonical email

		fetch_canonical = ("SELECT canonical "
			"FROM aliases "
			"WHERE alias=%s "
			"AND active = TRUE")

		cfg.cursor_people.execute(fetch_canonical, (email, ))
		cfg.db_people.commit()

		canonical = list(cfg.cursor_people)

		if canonical:
			for email in canonical:
				return email['canonical']
		else:
			return email

### The real function starts here ###

	cfg.update_status('Filling empty affiliations')
	cfg.log_activity('Info','Filling empty affiliations')

	# Process any changes to the affiliations or aliases, and set any existing
	# entries in analysis_data to NULL so they are filled properly.

	# First, get the time we started fetching since we'll need it later

	cfg.cursor.execute("SELECT current_timestamp(6) as fetched")

	affiliations_fetched = cfg.cursor.fetchone()[0]#['fetched']

	# Now find the last time we worked on affiliations, to figure out what's new

	affiliations_processed = cfg.get_setting('affiliations_processed')

	get_changed_affiliations = ("SELECT domain FROM affiliations WHERE "
		"last_modified >= %s")

	cfg.cursor_people.execute(get_changed_affiliations, (affiliations_processed, ))

	changed_affiliations = list(cfg.cursor_people)

	# Process any affiliations which changed since we last checked

	for changed_affiliation in changed_affiliations:

		cfg.log_activity('Debug','Resetting affiliation for %s' %
			changed_affiliation['domain'])

		set_author_to_null = ("UPDATE analysis_data SET author_affiliation = NULL "
			"WHERE author_email LIKE CONCAT('%%',%s)")

		cfg.cursor.execute(set_author_to_null, (changed_affiliation['domain'], ))
		cfg.db.commit()

		set_committer_to_null = ("UPDATE analysis_data SET committer_affiliation = NULL "
			"WHERE committer_email LIKE CONCAT('%%',%s)")

		cfg.cursor.execute(set_committer_to_null, (changed_affiliation['domain'], ))
		cfg.db.commit()

	# Update the last fetched date, so we know where to start next time.

	update_affiliations_date = ("UPDATE settings SET value=%s "
		"WHERE setting = 'affiliations_processed'")

	cfg.cursor.execute(update_affiliations_date, (affiliations_fetched, ))
	cfg.db.commit()

	# On to the aliases, now

	# First, get the time we started fetching since we'll need it later

	cfg.cursor.execute("SELECT current_timestamp(6) as fetched")

	aliases_fetched = cfg.cursor.fetchone()[0]#['fetched']

	# Now find the last time we worked on aliases, to figure out what's new

	aliases_processed = cfg.get_setting('aliases_processed')

	get_changed_aliases = ("SELECT alias FROM aliases WHERE "
		"last_modified >= %s")

	cfg.cursor_people.execute(get_changed_aliases, (aliases_processed, ))

	changed_aliases = list(cfg.cursor_people)

	# Process any aliases which changed since we last checked

	for changed_alias in changed_aliases:

		cfg.log_activity('Debug','Resetting affiliation for %s' %
			changed_alias['alias'])

		set_author_to_null = ("UPDATE analysis_data SET author_affiliation = NULL "
			"WHERE author_raw_email LIKE CONCAT('%%',%s)")

		cfg.cursor.execute(set_author_to_null,(changed_alias['alias'], ))
		cfg.db.commit()

		set_committer_to_null = ("UPDATE analysis_data SET committer_affiliation = NULL "
			"WHERE committer_raw_email LIKE CONCAT('%%',%s)")

		cfg.cursor.execute(set_committer_to_null, (changed_alias['alias'], ))
		cfg.db.commit()

		reset_author = ("UPDATE analysis_data "
			"SET author_email = %s "
			"WHERE author_raw_email = %s")

		cfg.cursor.execute(reset_author, (discover_alias(changed_alias['alias']),changed_alias['alias']))
		cfg.db.commit

		reset_committer = ("UPDATE analysis_data "
			"SET committer_email = %s "
			"WHERE committer_raw_email = %s")

		cfg.cursor.execute(reset_committer,	(discover_alias(changed_alias['alias']),changed_alias['alias']))
		cfg.db.commit

	# Update the last fetched date, so we know where to start next time.

	update_aliases_date = ("UPDATE settings SET value=%s "
		"WHERE setting = 'aliases_processed'")

	cfg.cursor.execute(update_aliases_date, (aliases_fetched, ))
	cfg.db.commit()

	# Now rebuild the affiliation data

	working_author = cfg.get_setting('working_author')

	if working_author != 'done':
		cfg.log_activity('Error','Trimming author data in affiliations: %s' %
			working_author)
		trim_author(cfg, working_author)

	# Figure out which projects have NULL affiliations so they can be recached

	set_recache = ("""UPDATE projects 
				SET recache=TRUE  
				FROM projects x, repos y, analysis_data z 
				where x.id = y.projects_id 
				and
				y."id" = z.repos_id
				and 
        (z.author_affiliation IS NULL OR 
        z.committer_affiliation IS NULL)""")

	# ("UPDATE projects p "
	# 	"JOIN repos r ON p.id = r.projects_id "
	# 	"JOIN analysis_data a ON r.id = a.repos_id "
	# 	"SET recache=TRUE WHERE "
	# 	"author_affiliation IS NULL OR "
	# 	"committer_affiliation IS NULL")
	cfg.cursor.execute(set_recache)
	cfg.db.commit()

	# Find any authors with NULL affiliations and fill them

	find_null_authors = ("SELECT DISTINCT author_email AS email, "
		"MIN(author_date) AS earliest "
		"FROM analysis_data "
		"WHERE author_affiliation IS NULL "
		"GROUP BY author_email")

	cfg.cursor.execute(find_null_authors)

	null_authors = list(cfg.cursor)

	cfg.log_activity('Debug','Found %s authors with NULL affiliation' %
		len(null_authors))

	for null_author in null_authors:

		email = null_author['email']

		store_working_author(cfg, email)

		discover_null_affiliations('author',email)

	store_working_author(cfg, 'done')

	# Find any committers with NULL affiliations and fill them

	find_null_committers = ("SELECT DISTINCT committer_email AS email, "
		"MIN(committer_date) AS earliest "
		"FROM analysis_data "
		"WHERE committer_affiliation IS NULL "
		"GROUP BY committer_email")

	cfg.cursor.execute(find_null_committers)

	null_committers = list(cfg.cursor)

	cfg.log_activity('Debug','Found %s committers with NULL affiliation' %
		len(null_committers))

	for null_committer in null_committers:

		email = null_committer['email']

		store_working_author(cfg, email)

		discover_null_affiliations('committer',email)

	# Now that we've matched as much as possible, fill the rest as (Unknown)

	fill_unknown_author = ("UPDATE analysis_data "
		"SET author_affiliation = '(Unknown)' "
		"WHERE author_affiliation IS NULL")

	cfg.cursor.execute(fill_unknown_author)
	cfg.db.commit()

	fill_unknown_committer = ("UPDATE analysis_data "
		"SET committer_affiliation = '(Unknown)' "
		"WHERE committer_affiliation IS NULL")

	cfg.cursor.execute(fill_unknown_committer)
	cfg.db.commit()

	store_working_author(cfg, 'done')

	cfg.log_activity('Info','Filling empty affiliations (complete)')

def invalidate_caches(cfg):

# Invalidate all caches

	cfg.update_status('Invalidating caches')
	cfg.log_activity('Info','Invalidating caches')

	invalidate_cache = "UPDATE projects SET recache = TRUE"
	cfg.cursor.execute(invalidate_cache)
	cfg.db.commit()

	cfg.log_activity('Info','Invalidating caches (complete)')

def rebuild_unknown_affiliation_and_web_caches(cfg):

# When there's a lot of analysis data, calculating display data on the fly gets
# pretty expensive. Instead, we crunch the data based upon the user's preferred
# statistics (author or committer) and store them. We also store all records
# with an (Unknown) affiliation for display to the user.

	cfg.update_status('Caching data for display')
	cfg.log_activity('Info','Caching unknown affiliations and web data for display')

	report_date = cfg.get_setting('report_date')
	report_attribution = cfg.get_setting('report_attribution')

	# Clear stale caches

	clear_project_weekly_cache = ("""
			DELETE 
				FROM
					project_weekly_cache C USING projects P 
				WHERE
					P.ID = C.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM project_weekly_cache c "
	# 	"JOIN projects p ON c.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_project_weekly_cache)
	cfg.db.commit()

	clear_project_monthly_cache = ("""
			DELETE 
				FROM
					project_monthly_cache C USING projects P 
				WHERE
					P.ID = C.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM project_monthly_cache c "
	# 	"JOIN projects p ON c.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_project_monthly_cache)
	cfg.db.commit()

	clear_project_annual_cache = ("""
			DELETE 
				FROM
					project_annual_cache C USING projects P 
				WHERE
					P.ID = C.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM project_annual_cache c "
	# 	"JOIN projects p ON c.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_project_annual_cache)
	cfg.db.commit()

	clear_repo_weekly_cache = ("""
			DELETE 
				FROM
					repo_weekly_cache C USING repos r,
					projects P 
				WHERE
					C.repos_id = r.ID 
					AND P.ID = r.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM repo_weekly_cache c "
	# 	"JOIN repos r ON c.repos_id = r.id "
	# 	"JOIN projects p ON r.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_repo_weekly_cache)
	cfg.db.commit()

	clear_repo_monthly_cache = ("""
			DELETE 
				FROM
					repo_monthly_cache C USING repos r,
					projects P 
				WHERE
					C.repos_id = r.ID 
					AND P.ID = r.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM repo_monthly_cache c "
	# 	"JOIN repos r ON c.repos_id = r.id "
	# 	"JOIN projects p ON r.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_repo_monthly_cache)
	cfg.db.commit()

	clear_repo_annual_cache = ("""
			DELETE 
				FROM
					repo_annual_cache C USING repos r,
					projects P 
				WHERE
					C.repos_id = r.ID 
					AND P.ID = r.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM repo_annual_cache c "
	# 	"JOIN repos r ON c.repos_id = r.id "
	# 	"JOIN projects p ON r.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_repo_annual_cache)
	cfg.db.commit()

	clear_unknown_cache = ("""
			DELETE 
				FROM
					unknown_cache C USING projects P 
				WHERE
					P.ID = C.projects_id 
					AND P.recache = TRUE
		""")

	# ("DELETE c.* FROM unknown_cache c "
	# 	"JOIN projects p ON c.projects_id = p.id WHERE "
	# 	"p.recache=TRUE")
	cfg.cursor.execute(clear_unknown_cache)
	cfg.db.commit()

	cfg.log_activity('Verbose','Caching unknown authors and committers')

	# Cache the unknown authors

	unknown_authors = ("INSERT INTO unknown_cache "
		"SELECT 'author', "
		"r.projects_id, "
		"a.author_email, "
		"SPLIT_PART(a.author_email,'@',-1), "
		"SUM(a.added) "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"WHERE a.author_affiliation = '(Unknown)' "
		"AND p.recache = TRUE "
		"GROUP BY r.projects_id,a.author_email")

	cfg.cursor.execute(unknown_authors)
	cfg.db.commit()

	# Cache the unknown committers

	unknown_committers = ("INSERT INTO unknown_cache "
		"SELECT 'committer', "
		"r.projects_id, "
		"a.committer_email, "
		"SPLIT_PART(a.committer_email,'@',-1), "
		"SUM(a.added) "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"WHERE a.committer_affiliation = '(Unknown)' "
		"AND p.recache = TRUE "
		"GROUP BY r.projects_id,a.committer_email")

	cfg.cursor.execute(unknown_committers)
	cfg.db.commit()

	# Start caching by project

	cfg.log_activity('Verbose','Caching projects')

	cache_projects_by_week = ("INSERT INTO project_weekly_cache "
		"SELECT r.projects_id AS projects_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"WEEK(a.%s_date) AS week, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY week, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"projects_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cfg.cursor.execute(cache_projects_by_week)
	cfg.db.commit()

	cache_projects_by_month = ("INSERT INTO project_monthly_cache "
		"SELECT r.projects_id AS projects_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"MONTH(a.%s_date) AS month, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY month, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"projects_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cfg.cursor.execute(cache_projects_by_month)
	cfg.db.commit()

	cache_projects_by_year = ("INSERT INTO project_annual_cache "
		"SELECT r.projects_id AS projects_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY year, "
		"affiliation, "
		"a.%s_email,"
		"projects_id"
		% (report_attribution,report_attribution,
		report_date,report_attribution))

	cfg.cursor.execute(cache_projects_by_year)
	cfg.db.commit()

	# Start caching by repo

	cfg.log_activity('Verbose','Caching repos')

	cache_repos_by_week = ("INSERT INTO repo_weekly_cache "
		"SELECT a.repos_id AS repos_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"WEEK(a.%s_date) AS week, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY week, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"repos_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cfg.cursor.execute(cache_repos_by_week)
	cfg.db.commit()

	cache_repos_by_month = ("INSERT INTO repo_monthly_cache "
		"SELECT a.repos_id AS repos_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"MONTH(a.%s_date) AS month, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY month, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"repos_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cfg.cursor.execute(cache_repos_by_month)
	cfg.db.commit()

	cache_repos_by_year = ("INSERT INTO repo_annual_cache "
		"SELECT a.repos_id AS repos_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY year, "
		"affiliation, "
		"a.%s_email,"
		"repos_id"
		% (report_attribution,report_attribution,
		report_date,report_attribution))

	cfg.cursor.execute(cache_repos_by_year)
	cfg.db.commit()

	# Reset cache flags

	reset_recache = "UPDATE projects SET recache = FALSE"
	cfg.cursor.execute(reset_recache)
	cfg.db.commit()

	cfg.log_activity('Info','Caching unknown affiliations and web data for display (complete)')

### The real program starts here ###
