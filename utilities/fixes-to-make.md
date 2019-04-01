# Fixes to Make

1. update repos set status="New" where path=""; 
	- when something goes wrong during initial cloning you can get the repo set to "Update", but without a path and having ever cloned the repo. So we need to check this. 
2. Empty Repos (repo exists but is empty on GitHub)
    - select * from repos where status != "Analyze";
    - update repos set status = "New" where status != "Analyze" and projects_id = 84; 
3. When first doing a bunch of new repos, if the repos are initially set to new, they all get set to "update" while facade-worker.py is going through them.  If one of them is empty or cannot be cloned (bitbucket seems to be problematic, for example), then on the next run facade-worker.py tries to update the repos, but they have no path and it shits the bed ...
    - update repos set status = "New" where path is null and status = "Update"; 
4. Repo links that can't be cloned: `cat facade.err | grep fatal:`

