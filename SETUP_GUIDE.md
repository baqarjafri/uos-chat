# 🚀 Stirling Chat MVP - Setup Guide

This guide will help you set up the development environment step by step.

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ **Python 3.11+** installed (You have: 3.13.7)
- ✅ **Docker** installed (You have: 28.4.0)
- ✅ **Git** installed (You have: 2.51.0)

---

## 🎯 Quick Setup (Automated)

Run the setup script to automate everything:

```powershell
.\setup.ps1
```

This will:
1. Configure Git with your name and email
2. Create Python virtual environment
3. Install all dependencies
4. Create .env file from template
5. Start PostgreSQL with Docker
6. Test database connection
7. Make initial Git commit

---

## 📖 Manual Setup (Step by Step)

If you prefer to understand each step:

### Step 1: Configure Git

```powershell
# Set your Git identity (for this project only)
git config user.name "Baqar"
git config user.email "your-email@example.com"

# Verify configuration
git config user.name
git config user.email
```

**Git Basics Reminder:**
- `git config` sets configuration values
- Without `--global`, settings apply only to current repository
- With `--global`, settings apply to all your repositories

### Step 2: Create Python Virtual Environment

```powershell
# Create virtual environment named 'venv'
python -m venv venv
```

**Virtual Environment Basics:**
- Isolates project dependencies from system Python
- Prevents version conflicts between projects
- Makes project portable and reproducible

### Step 3: Activate Virtual Environment

```powershell
# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1

# You'll see (venv) prefix in your terminal
```

**Why Activate?**
- All `pip install` commands install to venv, not system
- Uses venv's Python interpreter
- Keeps your system Python clean

### Step 4: Install Dependencies

```powershell
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**What Gets Installed:**
- FireCrawl SDK (web scraping)
- PostgreSQL drivers (psycopg2, pgvector)
- OpenAI SDK (embeddings)
- Anthropic SDK (Claude 3 Haiku)
- LangChain (RAG framework)
- FastAPI (web framework)
- And more... (see requirements.txt)

### Step 5: Create .env File

```powershell
# Copy template to .env
Copy-Item .env.example .env

# Edit .env and add your API keys
notepad .env
```

**Required API Keys:**
1. **FIRECRAWL_API_KEY** - Get from https://firecrawl.dev
2. **OPENAI_API_KEY** - Get from https://platform.openai.com/api-keys
3. **ANTHROPIC_API_KEY** - Get from https://console.anthropic.com/

**⚠️ IMPORTANT:** Never commit .env to Git! It's already in .gitignore.

### Step 6: Start PostgreSQL with Docker

```powershell
# Start PostgreSQL container in background
docker-compose up -d

# Check if container is running
docker ps

# View logs
docker-compose logs -f postgres
```

**Docker Compose Basics:**
- `up -d` starts services in detached mode (background)
- `down` stops and removes containers
- `logs` shows container output
- `ps` lists running containers

**What's Running:**
- PostgreSQL 16 with pgvector extension
- Container name: `stirling_chat_db`
- Port: 5432 (mapped to host)
- Database: `stirling_chat`
- User: `postgres`
- Password: `stirling_dev_2024`

### Step 7: Test Database Connection

```powershell
# Connect to PostgreSQL
docker exec -it stirling_chat_db psql -U postgres -d stirling_chat

# Inside psql, test pgvector
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

# Exit psql
\q
```

**PostgreSQL Basics:**
- `psql` is the PostgreSQL interactive terminal
- `\l` lists all databases
- `\dt` lists all tables
- `\q` quits psql
- `\?` shows help

### Step 8: Make Initial Git Commit

```powershell
# Check what files will be committed
git status

# Add all files to staging
git add .

# Create initial commit
git commit -m "Initial commit: Project setup with Docker PostgreSQL, environment config, and URL organization"

# View commit history
git log --oneline
```

**Git Basics Reminder:**
- `git status` shows changed files
- `git add .` stages all changes
- `git commit -m "message"` creates a commit
- `git log` shows commit history
- `git diff` shows changes

---

## 🔍 Verification Checklist

After setup, verify everything works:

- [ ] Virtual environment activated (see `(venv)` in terminal)
- [ ] Dependencies installed (`pip list` shows packages)
- [ ] .env file created with API keys
- [ ] Docker container running (`docker ps` shows `stirling_chat_db`)
- [ ] PostgreSQL accessible (can connect with psql)
- [ ] pgvector extension enabled (query returns version)
- [ ] Git configured (check with `git config user.name`)
- [ ] Initial commit created (`git log` shows commit)

---

## 🛠️ Useful Commands

### Virtual Environment

```powershell
# Activate
.\venv\Scripts\Activate.ps1

# Deactivate
deactivate

# Install new package
pip install package-name

# Save dependencies
pip freeze > requirements.txt
```

### Docker

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Remove volumes (⚠️ deletes data!)
docker-compose down -v
```

### PostgreSQL

```powershell
# Connect to database
docker exec -it stirling_chat_db psql -U postgres -d stirling_chat

# Backup database
docker exec stirling_chat_db pg_dump -U postgres stirling_chat > backup.sql

# Restore database
docker exec -i stirling_chat_db psql -U postgres -d stirling_chat < backup.sql
```

### Git

```powershell
# Check status
git status

# View changes
git diff

# Add files
git add filename
git add .

# Commit changes
git commit -m "Your message"

# View history
git log --oneline
git log --graph --oneline --all

# Create branch
git branch feature-name
git checkout -b feature-name

# Switch branch
git checkout branch-name
```

---

## 🐛 Troubleshooting

### Virtual Environment Won't Activate

**Error:** "Execution of scripts is disabled on this system"

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker Container Won't Start

**Error:** "Port 5432 is already in use"

**Solution:**
```powershell
# Stop existing PostgreSQL service
# Or change port in docker-compose.yml to "5433:5432"
```

### Can't Connect to Database

**Error:** "Connection refused"

**Solution:**
```powershell
# Check if container is running
docker ps

# Check container logs
docker-compose logs postgres

# Restart container
docker-compose restart
```

### Git Commit Fails

**Error:** "Author identity unknown"

**Solution:**
```powershell
# Set Git identity
git config user.name "Your Name"
git config user.email "your@email.com"
```

---

## 📚 Learning Resources

### Git Version Control
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [Git Branching](https://learngitbranching.js.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

### Docker
- [Docker Get Started](https://docs.docker.com/get-started/)
- [Docker Compose](https://docs.docker.com/compose/)

### Python Virtual Environments
- [Python venv](https://docs.python.org/3/library/venv.html)
- [pip Documentation](https://pip.pypa.io/en/stable/)

### PostgreSQL
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

---

## ✅ Next Steps

Once setup is complete:

1. **Add API Keys** to `.env` file
2. **Test Database** connection
3. **Proceed to Step 3** in MVP_PLAN.md: Implement FireCrawl scraper

---

## 📞 Need Help?

If you encounter issues:
1. Check the Troubleshooting section above
2. Review error messages carefully
3. Check Docker and Python logs
4. Verify all prerequisites are installed

Happy coding! 🚀
