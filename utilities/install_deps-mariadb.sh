#!/bin/bash

echo "
This script will install the necessary dependencies to run Facade in headless
mode. This means that it will not install Apache or the required PHP packages.
You must use the CLI to configure Facade and export analysis data, which is
available in cli/facade.py

You can always convert to a full installation by running the full script to fill
in any missing packages, should you change your mind later:
 $ ./install_deps-deb-full.sh

Installing any missing dependencies...
"

sudo apt-get install mariadb-server \
python3 python3-mysqldb python3-bcrypt python3-xlsxwriter python3-texttable

echo "
If everything went well, your next step is to run setup:
 $ ./setup.py
 "

