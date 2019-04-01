# Fixes to Make

1. update repos set status="New" where path=""; 
	- when something goes wrong during initial cloning you can get the repo set to "Update", but without a path and having ever cloned the repo. So we need to check this. 