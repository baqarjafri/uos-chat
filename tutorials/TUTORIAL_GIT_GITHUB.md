# Git & GitHub Tutorial: Stirling Chat Project

## 🎯 Your Journey

This tutorial takes you through the **complete journey** of:

1. Creating a GitHub repository
2. Pushing your Stirling Chat code to GitHub
3. Making changes in Windsurf IDE
4. Pushing updates to GitHub
5. Connecting to Railway.app for deployment

---

## 📚 Quick Concepts (2 minutes)

| Git                          | GitHub                        |
| ---------------------------- | ----------------------------- |
| Software on your computer    | Website that stores your code |
| Tracks every change you make | Lets you share & collaborate  |
| Works offline                | Needs internet                |

**Think of it like this:**

- **Git** = Save button with unlimited undo history
- **GitHub** = Google Drive for code

---

# PHASE 1: ONE-TIME SETUP

## Step 1.1: Check Git is Installed

Open **Windsurf Terminal** (Ctrl + `) and run:

```bash
git --version
```

✅ **Expected output:** `git version 2.x.x`

❌ **If not installed:** Download from https://git-scm.com/downloads

## Step 1.2: Configure Your Identity

Run these commands (replace with your info):

```bash
git config --global user.name "Ghulam"
git config --global user.email "your.email@example.com"
```

✅ **Verify:**

```bash
git config --list
```

---

# PHASE 2: CREATE GITHUB REPOSITORY

## Step 2.1: Create GitHub Account

1. Go to **https://github.com/signup**
2. Sign up with your email
3. Verify your email

## Step 2.2: Create Personal Access Token (IMPORTANT!)

GitHub no longer accepts passwords. You need a token:

1. Go to **https://github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Give it a name: `Windsurf Access`
4. Set expiration: **90 days** (or "No expiration" for convenience)
5. Check these scopes:
   - ✅ `repo` (Full control of private repositories)
6. Click **"Generate token"**
7. **COPY THE TOKEN NOW** - you won't see it again!
8. Save it somewhere safe (password manager, notepad)

## Step 2.3: Create New Repository on GitHub

1. Go to **https://github.com/new**
2. Fill in:
   - **Repository name:** `stirling-chat`
   - **Description:** `University of Stirling AI Chatbot MVP`
   - **Visibility:** `Private` (recommended for now)
   - ❌ **DO NOT** check "Add a README file"
   - ❌ **DO NOT** check "Add .gitignore"
   - ❌ **DO NOT** choose a license
3. Click **"Create repository"**

✅ **You'll see a page with setup instructions - keep this open!**

---

# PHASE 3: PUSH STIRLING CHAT TO GITHUB

## Step 3.1: Open Terminal in Windsurf

1. In Windsurf, press `Ctrl + `` (backtick) to open terminal
2. Navigate to your project:

```bash
cd c:\Users\Ghulam\CascadeProjects\stirling_chat
```

## Step 3.2: Initialize Git Repository

```bash
git init
```

✅ **Expected output:** `Initialized empty Git repository in ...`

## Step 3.3: Check What Files Will Be Tracked

```bash
git status
```

You'll see lots of red files. That's normal - these are untracked files.

**Important:** Your `.gitignore` file already excludes:

- `venv/` - Python virtual environment
- `node_modules/` - npm packages
- `.env` - Your secret API keys
- `__pycache__/` - Python cache

## Step 3.4: Stage All Files

```bash
git add .
```

The `.` means "everything in current folder".

✅ **Verify:**

```bash
git status
```

Now files should be **green** (staged).

## Step 3.5: Create First Commit

```bash
git commit -m "Initial commit: Stirling University AI Chatbot MVP"
```

✅ **Expected output:** Shows files committed, like:

```
[main (root-commit) abc1234] Initial commit: Stirling University AI Chatbot MVP
 50 files changed, 5000 insertions(+)
```

## Step 3.6: Connect to GitHub

Replace `YOUR_GITHUB_USERNAME` with your actual username:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/stirling-chat.git
```

## Step 3.7: Push to GitHub

```bash
git branch -M main
git push -u origin main
```

**When prompted:**

- **Username:** Your GitHub username
- **Password:** Paste your **Personal Access Token** (not your password!)

✅ **Expected output:**

```
Enumerating objects: 100, done.
Counting objects: 100% (100/100), done.
Writing objects: 100% (100/100), 500.00 KiB | 10.00 MiB/s, done.
To https://github.com/YOUR_USERNAME/stirling-chat.git
 * [new branch]      main -> main
```

## Step 3.8: Verify on GitHub

1. Go to `https://github.com/YOUR_USERNAME/stirling-chat`
2. Refresh the page
3. 🎉 **Your code is now on GitHub!**

---

# PHASE 4: MAKE CHANGES & PUSH AGAIN

Now let's practice the daily workflow of making changes and pushing them.

## Step 4.1: Make a Small Change in Windsurf

Let's update the README. In Windsurf:

1. Open `README.md`
2. Add this line at the top:

```markdown
# Stirling University AI Chatbot

> An intelligent chatbot for prospective students at the University of Stirling.
```

3. Save the file (Ctrl + S)

## Step 4.2: Check What Changed

In terminal:

```bash
git status
```

✅ **Expected output:**

```
modified:   README.md
```

## Step 4.3: See the Actual Changes

```bash
git diff README.md
```

This shows exactly what lines were added/removed.

## Step 4.4: Stage the Change

```bash
git add README.md
```

Or stage everything:

```bash
git add .
```

## Step 4.5: Commit the Change

```bash
git commit -m "Update README with project description"
```

**Good commit messages:**

- ✅ `"Fix chat widget not showing on mobile"`
- ✅ `"Add fullscreen mode to chat"`
- ✅ `"Update RAG prompt for better responses"`
- ❌ `"Fixed stuff"`
- ❌ `"Update"`

## Step 4.6: Push to GitHub

```bash
git push
```

(You don't need `origin main` anymore after the first push)

## Step 4.7: Verify on GitHub

1. Go to your repository on GitHub
2. Click on `README.md`
3. You should see your changes!

---

# PHASE 5: DAILY WORKFLOW SUMMARY

## The 4-Step Cycle

Every time you make changes:

```bash
# 1. Check what changed
git status

# 2. Stage changes
git add .

# 3. Commit with message
git commit -m "Describe what you changed"

# 4. Push to GitHub
git push
```

## Windsurf Shortcuts

Windsurf has built-in Git support:

1. **Source Control Panel:** Click the branch icon in left sidebar (or Ctrl+Shift+G)
2. **Stage files:** Click `+` next to changed files
3. **Commit:** Type message in box, click ✓ checkmark
4. **Push:** Click `...` menu → Push

---

# PHASE 6: CONNECT TO RAILWAY.APP

Once your code is on GitHub, deploying to Railway is easy:

## Step 6.1: Create Railway Account

1. Go to **https://railway.app**
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway to access your GitHub

## Step 6.2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Find and select `stirling-chat`
4. Railway will auto-detect and start deploying!

## Step 6.3: Auto-Deploy on Push

Railway automatically redeploys when you push to GitHub!

**Workflow:**

1. Make changes in Windsurf
2. `git add . && git commit -m "message" && git push`
3. Railway detects the push and redeploys automatically
4. Your live site updates in ~2 minutes

---

# 🆘 TROUBLESHOOTING

## Problem: "Authentication failed"

```
Make sure you're using your Personal Access Token, not your password.
The token looks like: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Problem: "Repository not found"

```bash
# Check your remote URL
git remote -v

# Fix if wrong
git remote set-url origin https://github.com/YOUR_USERNAME/stirling-chat.git
```

## Problem: "Push rejected"

```bash
# Pull first, then push
git pull origin main
git push
```

## Problem: "Accidentally committed .env"

```bash
# Remove from Git but keep file locally
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

## Problem: "Want to undo last commit"

```bash
# Undo commit but keep changes
git reset --soft HEAD~1
```

---

# 📋 QUICK REFERENCE

| Command                 | What it does         |
| ----------------------- | -------------------- |
| `git status`          | See what's changed   |
| `git add .`           | Stage all changes    |
| `git commit -m "msg"` | Save a snapshot      |
| `git push`            | Upload to GitHub     |
| `git pull`            | Download from GitHub |
| `git log --oneline`   | See history          |
| `git diff`            | See what changed     |

---

# ✅ CHECKLIST

## One-Time Setup

- [X] Git installed (`git --version`)
- [X] Git configured (`git config --global user.name/email`)
- [X] GitHub account created
- [X] Personal Access Token generated and saved
- [X] Repository created on GitHub
- [X] Local project pushed to GitHub

## Daily Workflow

- [ ] Make changes in Windsurf
- [ ] `git add .`
- [ ] `git commit -m "description"`
- [ ] `git push`
- [ ] Verify on GitHub

---

**Next:** Read `TUTORIAL_DOCKER.md` to understand Docker, then `TUTORIAL_DEPLOYMENT.md` for full Railway deployment.
