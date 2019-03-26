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

# Reset a stuck status
#
# The facade-worker.py script will only run if the status in the db is idle. If
# it is killed halfway through, this can leave it in an erroneous state. This
# script resets it. Only run it if you know no analysis is actually running,
# otherwise you'll thrash your machine.

import MySQLdb
import configparser

try:
	config = configparser.ConfigParser()
	config.read('db.cfg')

	# Read in the people connection info

	db_user = config['main_database']['user']
	db_pass = config['main_database']['pass']
	db_name = config['main_database']['name']
	db_host = config['main_database']['host']

	db = MySQLdb.connect(
		host = db_host,
		user = db_user,
		passwd = db_pass,
		db = db_name,
		charset = 'utf8mb4')

	cursor = db.cursor(MySQLdb.cursors.DictCursor)

except:
	sys.exit("It appears you haven't run setup.py yet. Please do this.")


query = "UPDATE settings SET value='Idle' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

query = ("INSERT INTO utility_log (level,status) VALUES "
	"('Error','facade-worker.py manually reset')")
cursor.execute(query)
db.commit()

cursor.close()
db.close()

