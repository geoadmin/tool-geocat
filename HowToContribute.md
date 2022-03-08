:warning: **This is a public repository ! Do not push sensitive information (password, username, token, e-mail,...)** :warning:
# Add a new Tool
If you want to add a new tool to this repository, please respect the following guidelines :
* Keep the same structure (i.e. one folder per tool)
* Document your tool with a dedicated README.md file at the root of your new folder
* Adapt the main README.md file (at the root of the repository) with your new tool (title and short description)

:warning: **The main branch is protected ! No direct push allowed ! Merge to the main branch needs to be reviewed by reo !** :warning:
# Use git to contribute (for git beginners)
If you don't already have a git folder corresponding to this repository, clone it to a dedicated directory :
```
git clone https://github.com/geoadmin/tool-geocat.git {folder-name}
```
If you do have a git directory matching this repo history, you can just pull the differences from GitHub :
```
git pull 
```
Do your stuff, create a new tool, fix/update/improve an exisiting one, then :
```
git checkout -b {new-branch-name}  # create a new branch
git add {the-files-you-want-to-push}  # add all files you want to commit
git commit -m "comments your commit"  # commit all your files and comment the commit
git push -u origin {new-branch-name}  # push your files to the remote
```
This will create a new branch on GitHub. You can ask reo to merge this new branch to the main one. Once merged, you can delete the newly created branch in GitHub. To keep your git folder up-to-date (matching history), do the following :
```
git checkout main  # go back to the main branch
git pull  # pull differences from GitHub (i.e. the new merge)
git branch -d {new-branch-name}  # Delete local {new-branch-name} branch
git branch -d -r origin/{new-branch-name}  # delete remote {new-branch-name} branch on local git directory - nothing is deleted on github
```
