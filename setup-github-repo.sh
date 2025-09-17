#!/bin/bash

# GitHub Repository Setup Script
# Run this after: gh auth login

set -e

echo "🚀 Setting up GitHub repository for AWS/Kubernetes guides..."

# Navigate to the directory
cd /Users/maripeddisupraj/Downloads/aws-stuff

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Create .gitignore
cat > .gitignore << 'EOF'
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo
*~

# Temporary files
*.tmp
*.temp
EOF

# Add all files
echo "📝 Adding files to git..."
git add .

# Commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Comprehensive AWS and Kubernetes guides

- AWS Best Practices Interview Guide
- AWS WAF Learning Guide  
- Cost Optimization Scenarios
- EKS Security Best Practices
- EKS Logging Strategies
- EKS Zero-Downtime Upgrades
- EKS PVC & EBS CSI Driver Guide
- Karpenter Complete Guide
- EKS Cluster Access Guide
- Kubecost with EKS Guide"

# Create GitHub repository
echo "🌐 Creating GitHub repository..."
gh repo create aws-kubernetes-guides \
    --public \
    --description "Comprehensive AWS and Kubernetes guides for interviews and production environments" \
    --clone=false

# Set main branch
git branch -M main

# Add remote and push
echo "⬆️ Pushing to GitHub..."
git remote add origin https://github.com/$(gh api user --jq .login)/aws-kubernetes-guides.git
git push -u origin main

echo "✅ Repository created successfully!"
echo "🔗 Repository URL: https://github.com/$(gh api user --jq .login)/aws-kubernetes-guides"
echo ""
echo "📋 Repository contains:"
echo "   • 10 comprehensive guides"
echo "   • Interview scenarios with real-world examples"
echo "   • Production-ready configurations"
echo "   • Step-by-step implementations"