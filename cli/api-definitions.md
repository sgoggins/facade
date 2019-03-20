# Define Flask APIs for these functions
	- functions in cli/facade.py
		- add_project(name,description,website,db,cursor)
		- delete_project(project_id,db,cursor)
		- add_repo(project_id,git_repo,db,cursor)
		- delete_repo(git_repo,db,cursor)
		- add_alias(alias,canonical,db,cursor)
		- delete_alias(alias_id,db,cursor)
		- add_affiliation(domain,affiliation,db,cursor,start_date = '')
		- delete_affiliation(affiliation_id,db,cursor)
		- get_setting(setting,db,cursor)
		- set_setting(setting,value,db,cursor)
		- add_tag(email,start_date,end_date,tag,db,cursor)
		- delete_tag(tag_id,db,cursor)

# Steps
	- Add facade.py as facade-cli.py in the data sources directory
	- in our existing facade.py you would add facade-cli.py you would define functions for calling the functions inside the library
	- Add the routes in a facade-cli-datasource.py file

