# Fixes to Make

1. update repos set status="New" where path=""; 
	- when something goes wrong during initial cloning you can get the repo set to "Update", but without a path and having ever cloned the repo. So we need to check this. 
2. Empty Repos (repo exists but is empty on GitHub)
    - select * from repos where status != "Analyze";
    - update repos set status = "New" where status != "Analyze" and projects_id = 84; 