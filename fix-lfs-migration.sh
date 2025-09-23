#!/bin/bash

# Fix Git LFS migration for existing repository
set -e

echo "🔧 Fixing Git LFS migration for large files..."

# Navigate to repository
cd /path/to/your/repository

# Remove the problematic GitHub remote temporarily
git remote remove github 2>/dev/null || true

# Install git-filter-repo if not available
if ! command -v git-filter-repo &> /dev/null; then
    echo "Installing git-filter-repo..."
    pip3 install git-filter-repo
fi

# Create backup branch
git branch backup-before-lfs-fix

# Set up Git LFS tracking for large files
echo "📋 Setting up Git LFS tracking..."
git lfs track "*.exe"
git lfs track "*.pbix"
git lfs track "*.json" --lockable

# Track files over 50MB specifically
git lfs track "CCC.Makalu.Tests.Data.Shared/Data/Chapters/*.json"
git lfs track "CCC.Makalu.Tools.VisualStudio.VehicleDataImport/*.exe"
git lfs track "PowerBI/*.pbix"

# Add .gitattributes
git add .gitattributes

# Migrate existing large files to LFS
echo "🔄 Migrating existing large files to LFS..."
git lfs migrate import --include="*.exe,*.pbix" --include-ref=refs/heads/master
git lfs migrate import --include="CCC.Makalu.Tests.Data.Shared/Data/Chapters/*.json" --include-ref=refs/heads/master

# Force push to origin (Azure DevOps)
echo "⬆️ Force pushing to origin..."
git push origin master --force

# Re-add GitHub remote
echo "🔗 Re-adding GitHub remote..."
git remote add github https://github.com/z-CCC-ONE-Sandbox/EstimatingLfs.git

# Push LFS objects first
echo "📦 Pushing LFS objects to GitHub..."
git lfs push github master --all

# Push repository
echo "⬆️ Pushing repository to GitHub..."
git push github master

echo "✅ Migration completed successfully!"
echo "🔍 Verify with: git lfs ls-files"