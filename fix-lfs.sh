#!/bin/bash

# Fix LFS for existing repository
cd /path/to/your/repository

# Remove GitHub remote
git remote remove github

# Install git-filter-repo
pip3 install git-filter-repo

# Migrate large files to LFS
git lfs track "*.exe" "*.pbix" "*.json"
git add .gitattributes
git lfs migrate import --include="*.exe,*.pbix" --include-ref=refs/heads/master

# Force push to origin, then re-add GitHub
git push origin master --force
git remote add github https://github.com/z-CCC-ONE-Sandbox/EstimatingLfs.git
git lfs push github master --all
git push github master