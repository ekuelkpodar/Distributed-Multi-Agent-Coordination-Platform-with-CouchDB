#!/bin/bash
# Automated GitHub setup script

set -e

echo "=========================================="
echo "GitHub Repository Setup"
echo "=========================================="
echo

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

# Check if already initialized
if [ -d .git ]; then
    echo "✓ Git repository already initialized"
else
    echo "Initializing git repository..."
    git init
    echo "✓ Git initialized"
fi

echo

# Check git config
if ! git config user.name &> /dev/null; then
    echo "Git user.name not set. Please configure:"
    read -p "Enter your name: " name
    git config user.name "$name"
fi

if ! git config user.email &> /dev/null; then
    echo "Git user.email not set. Please configure:"
    read -p "Enter your email: " email
    git config user.email "$email"
fi

echo "Git configured as: $(git config user.name) <$(git config user.email)>"
echo

# Show current status
echo "Current git status:"
git status --short
echo

# Ask to stage files
read -p "Stage all files? (y/n): " stage_files
if [ "$stage_files" = "y" ] || [ "$stage_files" = "Y" ]; then
    git add .
    echo "✓ Files staged"
    echo
    git status --short
    echo
fi

# Ask to commit
read -p "Create initial commit? (y/n): " create_commit
if [ "$create_commit" = "y" ] || [ "$create_commit" = "Y" ]; then
    git commit -m "Initial commit: Distributed Multi-Agent Coordination Platform

- Implemented 3-node CouchDB cluster with replication
- Built agent framework with lifecycle management
- Created task queue with priority scheduling and dependencies
- Added conflict resolution strategies (Vector Clock, LWW, Merge)
- Implemented coordination patterns (Map-Reduce, Pipeline, Auction)
- Set up monitoring with Prometheus and Grafana
- Added comprehensive tests and documentation
- Created working examples and setup scripts

Includes 32 files with ~3,000 lines of Python code and complete documentation."
    
    echo "✓ Initial commit created"
    echo
fi

# Check for existing remote
if git remote | grep -q "origin"; then
    echo "Remote 'origin' already exists:"
    git remote -v
    echo
    read -p "Remove existing remote and add new one? (y/n): " remove_remote
    if [ "$remove_remote" = "y" ] || [ "$remove_remote" = "Y" ]; then
        git remote remove origin
        echo "✓ Removed existing remote"
    else
        echo "Keeping existing remote. Skipping remote setup."
        exit 0
    fi
fi

# Ask for GitHub repository URL
echo
echo "=========================================="
echo "GitHub Repository Setup"
echo "=========================================="
echo
echo "First, create a repository on GitHub:"
echo "1. Go to https://github.com/new"
echo "2. Create a new repository (don't initialize with README)"
echo "3. Copy the repository URL"
echo
echo "Repository URL formats:"
echo "  HTTPS: https://github.com/USERNAME/REPO_NAME.git"
echo "  SSH:   git@github.com:USERNAME/REPO_NAME.git"
echo

read -p "Enter your GitHub repository URL: " repo_url

if [ -z "$repo_url" ]; then
    echo "Error: No URL provided"
    exit 1
fi

# Add remote
git remote add origin "$repo_url"
echo "✓ Added remote: $repo_url"
echo

# Verify remote
echo "Remote configured:"
git remote -v
echo

# Ask to push
read -p "Push to GitHub now? (y/n): " do_push
if [ "$do_push" = "y" ] || [ "$do_push" = "Y" ]; then
    echo
    echo "Pushing to GitHub..."
    
    # Set main branch
    git branch -M main
    
    # Push
    if git push -u origin main; then
        echo
        echo "=========================================="
        echo "✓ Successfully pushed to GitHub!"
        echo "=========================================="
        echo
        echo "Your repository is now available at:"
        echo "$repo_url" | sed 's/\.git$//'
        echo
        echo "Next steps:"
        echo "1. Visit your repository on GitHub"
        echo "2. Add topics/tags for discoverability"
        echo "3. Set up branch protection rules"
        echo "4. Star your own repo ⭐"
        echo
    else
        echo
        echo "=========================================="
        echo "Push failed!"
        echo "=========================================="
        echo
        echo "Common issues:"
        echo "1. Authentication: Use GitHub Personal Access Token"
        echo "2. SSH keys: Set up SSH keys for GitHub"
        echo "3. Repository exists: Pull first with --allow-unrelated-histories"
        echo
        echo "See GITHUB_SETUP.md for detailed troubleshooting"
        exit 1
    fi
else
    echo
    echo "Skipping push. You can push later with:"
    echo "  git branch -M main"
    echo "  git push -u origin main"
fi

echo
echo "Setup complete!"
