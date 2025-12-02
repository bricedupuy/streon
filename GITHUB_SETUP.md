# GitHub Setup Instructions

## Create GitHub Repository

1. **Go to GitHub**
   - Visit https://github.com/new
   - Or click the "+" icon in the top right → "New repository"

2. **Repository Settings**
   - **Repository name:** `streon`
   - **Description:** Professional Multi-Flow Audio Transport System for Radio Broadcasters
   - **Visibility:** Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. **Click "Create repository"**

## Push to GitHub

Once you've created the repository on GitHub, run these commands:

```bash
cd c:/Users/BriceDupuy/Code/streon-claude

# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/streon.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin master
```

## Alternative: Using GitHub CLI

If you have GitHub CLI installed:

```bash
cd c:/Users/BriceDupuy/Code/streon-claude

# Create repository and push
gh repo create streon --public --source=. --remote=origin --push
```

## After Pushing

1. Visit your repository: `https://github.com/YOUR_USERNAME/streon`
2. The README.md will be displayed on the main page
3. Check that all files are present

## Next Steps

1. **Add repository topics** on GitHub:
   - `audio`
   - `broadcast`
   - `radio`
   - `liquidsoap`
   - `srt`
   - `dante`
   - `aes67`
   - `python`
   - `react`
   - `typescript`

2. **Configure repository settings:**
   - Enable Issues
   - Enable Discussions (optional)
   - Set up branch protection rules (when ready)

3. **Add collaborators** (if needed):
   - Settings → Collaborators → Add people

## Repository URL

After creation, your repository will be at:
```
https://github.com/YOUR_USERNAME/streon
```

Clone URL:
```
https://github.com/YOUR_USERNAME/streon.git
```
