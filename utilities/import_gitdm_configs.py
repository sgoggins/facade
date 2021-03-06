#!/usr/bin/python3

# Copyright 2017-2018 Brian Warner
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
# This script enables you to import the control files from gitdm.

import sys
import MySQLdb
import imp
import os
import warnings
import getopt
import datetime
import configparser

def import_aliases(filename):

	safe = False

	with open(filename) as f:
		for line in f:

			# An unsophisticated test whether this seems to be an aliases file.

			if line.find('# This is the email aliases file') == 0:
				safe = True
				continue

			# Skip comments and empty lines

			if line.find('#') == 0 or len(line.strip()) == 0:
				continue

			# Trim comments

			if line.find('#') > 0:
				line = line[:line.find('#')]

			if safe:
				canonical = line.split()[-1]
				alias = line[:line.rfind(canonical)].strip()

				insert = ("INSERT INTO aliases (canonical,alias) VALUES "
					"(%s,%s) "
					"ON DUPLICATE KEY UPDATE active = TRUE")

				# Suppress warnings about duplicate entries

				with warnings.catch_warnings():
					warnings.simplefilter("ignore")

					cursor_people.execute(insert, (canonical,alias))
					db_people.commit()

			else:
				print ("This file failed a basic test and appears not to be an aliases\n"
					"file. If you are sure it's formatted correctly, you may want\n"
					"to append the contents of this file onto a fresh aliases file\n"
					"straight from the gitdm repository.\n\n%s\n" % filename)

def commit_affiliation(line):

# Helper function to quickly commit a line to the db.

	values = ()
	if line[2]:

		insert = ("INSERT INTO affiliations (domain,affiliation,start_date) "
			"VALUES (%s,%s,%s) "
			"ON DUPLICATE KEY UPDATE active = TRUE")

		values = (line[0],line[1],line[2])

	else:

		insert = ("INSERT INTO affiliations (domain,affiliation) "
			"VALUES (%s,%s) "
			"ON DUPLICATE KEY UPDATE active = TRUE")

		values = (line[0],line[1])

	# Suppress warnings about duplicate entries

	with warnings.catch_warnings():
		warnings.simplefilter("ignore")

		cursor_people.execute(insert, values)
		db_people.commit()

def bad_config(domain,first,second,filename):

	print ('\n*** WARNING: BAD EMAIL MAPPING. YOU NEED TO FIX THIS. ***\n\n'
		'This happens when you have an email or domain mapped to more than one\n'
		'affiliation without a date to establish order. For example:\n'
		'  dev@company.com	IBM\n'
		'  dev@company.com	Samsung\n\n'
		'You must add an end date to proceed further:\n'
		'  dev@company.com	IBM < 2011-01-06\n'
		'  dev@company.com	Samsung\n\n\n'
		'In this case, the offending lines in %s were:\n'
		'  %s -> %s\n  %s -> %s\n\n' % (filename,domain,first,domain,second))

	sys.exit(1)

def import_emailmap(filename):

	safe = False
	importfile = []

	with open(filename) as f:
		for line in f:

			# A simple, unsophisticated test whether this looks like an emailmap
			# file.

			if line.find('# Here is a set of mappings of domain names') == 0:
				safe = True
				continue

			# Skip comments and empty lines

			if line.find('#') == 0 or len(line.strip()) == 0:
				continue

			# Trim comments

			if line.find('#') > 0:
				line = line[:line.find('#')]

			if safe:

				domain = line.split()[0]
				# Add the domain/email

				remainder = line[len(domain):].strip().split("<")

				# Capture date, if it exists
				if len(remainder) == 2:
					(affiliation,end_date) = map(str.strip,remainder)
					if datetime.datetime.strptime(end_date,"%Y-%m-%d") > datetime.datetime.today():
						is_current = 1
				else:
					affiliation = remainder[0]
					end_date = '9999-12-31'

				importfile.append([domain,affiliation,end_date])

			else:
				print ("This file failed a basic test and appears not to be an emailmap\n"
					"file. If you are sure it's formatted correctly, you may want\n"
					"to append the contents of this file onto a fresh emailmap file\n"
					"straight from the gitdm repository.\n\n%s\n" % filename)
				sys.exit(1)

		# Dedupe the list (we don't a set since each line must stay mutable)

		deduped = []

		for line in importfile:
			if line not in deduped:
				deduped.append(line)

		# Sort by domain and date so we can convert end dates to start dates

		deduped.sort(key=lambda key: (key[0],key[2]), reverse=True)

		previous_line = ''
		latest_found = False

		for line in deduped:

			# Walk through the file. When a line matches the previous line, it's
			# part of a group of domain records with end dates and overlaps. In
			# that case, move the end date up one to the previous line, which
			# makes it a start date. When a line doesn't match its previous
			# line, it's either standalone or the earliest domain record. Either
			# way, the date info should be removed.

			if previous_line:
				if line[0] == previous_line[0]:

					if previous_line[2] == line[2]:

						bad_config(previous_line[0],previous_line[1],line[1],filename)

					# Convert the ending date to a starting date

					previous_line[2] = line[2]
					line[2] = ''

				else:
					previous_line[2] = ''

				commit_affiliation(previous_line)

			previous_line = line

		# If last item in file is standalone, clear the placeholder

		if line[2] == '9999-12-31':
			line[2] = ''

		commit_affiliation(previous_line)

def usage():

	print ("\nFacade can import emailmap and alias config files from gitdm. To\n"
		"import a config file, chose the appropriate type and its location.\n"
		"Config file entries already in the database will be ignored.\n\n"
		"Options:\n"
		"	-a <aliases filename\n"
		"	-e <emailmap filename\n\n"
		"Sample usage:\n"
		"	./import_gitdm_configs.py -a <filename> -e <filename>\n\n")

### The real program starts here ###

try:
	config = configparser.ConfigParser()
	config.read('db.cfg')

	# Read in the people connection info

	db_user_people = config['people_database']['user']
	db_pass_people = config['people_database']['pass']
	db_name_people = config['people_database']['name']
	db_host_people = config['people_database']['host']

	db_people = MySQLdb.connect(
		host = db_host_people,
		user = db_user_people,
		passwd = db_pass_people,
		db = db_name_people,
		charset = 'utf8mb4')

	cursor_people = db_people.cursor(MySQLdb.cursors.DictCursor)
except:
	sys.exit("It appears you haven't run setup.py yet. Please do this.")

try:
	opts,args = getopt.getopt(sys.argv[1:],'a:e:h')
except getopt.GetoptError as err:
	print (err)
	usage()
	sys.exit(2)

for opt,arg in opts:
	if opt == '-a':
		import_aliases(arg)
	elif opt == '-e':
		import_emailmap(arg)
	elif opt == '-h':
		usage()


