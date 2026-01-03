# GitHub Setup Guide

## Quick Setup (Automated)

Run this script to set up Git and push to GitHub:

```bash
./scripts/setup_github.sh
```

## Manual Setup

Follow these steps to add the project to GitHub:

### Step 1: Initialize Git Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
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
```

### Step 2: Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click "New repository" or visit https://github.com/new
3. Fill in:
   - **Repository name**: `distributed-agent-platform` (or your preferred name)
   - **Description**: "Production-ready distributed multi-agent coordination platform using CouchDB"
   - **Visibility**: Public or Private (your choice)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

### Step 3: Add Remote and Push

```bash
# Add GitHub remote (replace USERNAME and REPO_NAME)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Verify Upload

Visit your repository URL and verify:
- [ ] All files are present
- [ ] README.md displays correctly
- [ ] Documentation is accessible
- [ ] License file is recognized

## Using SSH (Recommended)

If you have SSH keys set up with GitHub:

```bash
# Add remote with SSH
git remote add origin git@github.com:USERNAME/REPO_NAME.git

# Push
git branch -M main
git push -u origin main
```

## Setting Up SSH Keys (If Needed)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start ssh-agent
eval "$(ssh-agent -s)"

# Add key to ssh-agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
# macOS:
pbcopy < ~/.ssh/id_ed25519.pub
# Linux:
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard

# Add to GitHub:
# 1. Go to GitHub.com → Settings → SSH and GPG keys
# 2. Click "New SSH key"
# 3. Paste your key and save
```

## Repository Settings (Optional)

After pushing, configure your repository:

### 1. Add Topics/Tags

Go to your repo → About → Settings (⚙️) and add topics:
- `distributed-systems`
- `multi-agent`
- `couchdb`
- `python`
- `coordination`
- `ai-agents`
- `eventual-consistency`
- `replication`

### 2. Set Up GitHub Actions (CI/CD)

Create `.github/workflows/tests.yml` for automated testing.

### 3. Enable GitHub Pages (For Documentation)

Settings → Pages → Source: Deploy from a branch → Select `main` and `/docs`

### 4. Add Branch Protection

Settings → Branches → Add rule:
- Branch name pattern: `main`
- [x] Require pull request reviews
- [x] Require status checks to pass

## .gitignore Verification

Ensure these are in `.gitignore` (already added):

```
__pycache__/
*.py[cod]
.env
.venv/
venv/
*.log
.pytest_cache/
htmlcov/
.coverage
*.db
.DS_Store
```

## Recommended Repository Description

```
Production-ready distributed multi-agent coordination platform leveraging 
CouchDB's conflict-free replication for autonomous AI agents across 
geographic regions. Features include priority task queues, vector clock 
conflict resolution, and Map-Reduce/Pipeline/Auction coordination patterns.
```

## Recommended README Badges

Add to the top of README.md:

```markdown
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## What Gets Pushed

The following structure will be uploaded:

```
distributed-agent-platform/
├── README.md
├── LICENSE
├── requirements.txt
├── docker-compose.yml
├── Makefile
├── pytest.ini
├── .gitignore
├── .env.example
├── GETTING_STARTED.md
├── PROJECT_SUMMARY.md
├── FILE_MANIFEST.md
├── GITHUB_SETUP.md
├── src/
│   ├── core/
│   ├── agents/
│   ├── database/
│   ├── coordination/
│   └── monitoring/
├── tests/
├── examples/
├── scripts/
├── docs/
└── config/
```

**Total size**: ~150 KB (excluding .git directory)

## Troubleshooting

### Error: "remote origin already exists"

```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/USERNAME/REPO_NAME.git
```

### Error: "failed to push some refs"

```bash
# Pull first (if repo has initial commit)
git pull origin main --allow-unrelated-histories

# Then push
git push -u origin main
```

### Error: "Authentication failed"

```bash
# Use GitHub Personal Access Token instead of password
# Generate token at: https://github.com/settings/tokens

# Or set up SSH keys (see above)
```

## Post-Upload Checklist

- [ ] Repository created on GitHub
- [ ] All files pushed successfully
- [ ] README displays correctly
- [ ] Links in README work
- [ ] License is detected
- [ ] Topics/tags added
- [ ] Description added
- [ ] Clone test: `git clone <your-repo-url>` works
- [ ] Share repository URL

## Next Steps After GitHub Upload

1. **Star your own repo** ⭐ (why not!)
2. **Share it** with collaborators
3. **Set up CI/CD** for automated testing
4. **Create releases** for version management
5. **Add a CONTRIBUTING.md** if accepting contributions
6. **Set up issue templates** for better bug reports
7. **Enable Discussions** for Q&A
8. **Add to your GitHub profile** README

## Repository URL Format

Your repository will be available at:
```
https://github.com/YOUR_USERNAME/REPO_NAME
```

Clone URL formats:
- HTTPS: `https://github.com/YOUR_USERNAME/REPO_NAME.git`
- SSH: `git@github.com:YOUR_USERNAME/REPO_NAME.git`
- GitHub CLI: `gh repo clone YOUR_USERNAME/REPO_NAME`

Enjoy sharing your distributed agent platform! 🚀
