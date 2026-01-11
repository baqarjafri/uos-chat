# Deployment Tutorial for Stirling Chat Project

## 📚 Overview

This guide walks you through deploying your Stirling Chat MVP to the cloud so anyone can access it via a URL.

**Goal:** Get your chatbot live at `https://stirling-chat.yourdomain.com`

---

## 🎯 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR DOMAIN                          │
│              stirling-chat.yourdomain.com               │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  RAILWAY.APP                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Frontend   │  │   Backend   │  │   PostgreSQL    │ │
│  │   (React)   │◄─┤  (FastAPI)  │◄─┤   + pgvector    │ │
│  │   :3000     │  │    :8000    │  │     :5432       │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Part 1: Prepare for Deployment

### 1.1 Create Backend Dockerfile

Your backend needs a Dockerfile. Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy scripts folder (needed for imports)
COPY ../scripts ./scripts

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Create Production docker-compose.yml

Create `docker-compose.prod.yml` in project root:

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 1.3 Update .gitignore

Make sure these are in your `.gitignore`:
```
.env
.env.local
.env.production
venv/
node_modules/
__pycache__/
*.pyc
.DS_Store
```

---

## 🌐 Part 2: Deploy to Railway.app

### Step 1: Push to GitHub First
```bash
cd c:\Users\Ghulam\CascadeProjects\stirling_chat
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### Step 2: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub (recommended)

### Step 3: Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Select your `stirling-chat` repository
4. Railway will auto-detect your project

### Step 4: Add PostgreSQL Database
1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway creates a PostgreSQL instance automatically

### Step 5: Configure Environment Variables
1. Click on your **Backend** service
2. Go to **"Variables"** tab
3. Add these variables:

```
DATABASE_URL=<copy from PostgreSQL service>
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
ENVIRONMENT=production
```

### Step 6: Configure Frontend Variables
1. Click on your **Frontend** service
2. Go to **"Variables"** tab
3. Add:

```
VITE_API_URL=<your backend URL from Railway>
```

### Step 7: Deploy
Railway auto-deploys when you push to GitHub!

### Step 8: Get Your URL
Railway provides URLs like:
- Frontend: `https://stirling-chat-frontend.up.railway.app`
- Backend: `https://stirling-chat-backend.up.railway.app`

---

## 🌍 Part 3: Custom Domain Setup

### 3.1 Buy a Domain
Recommended registrars:
- **Namecheap** (~$10/year for .com)
- **Cloudflare** (~$9/year, includes free SSL)
- **Google Domains** (~$12/year)

### 3.2 Connect Domain to Railway

1. In Railway, click your Frontend service
2. Go to **"Settings"** → **"Domains"**
3. Click **"+ Custom Domain"**
4. Enter: `chat.yourdomain.com`
5. Railway shows DNS records to add

### 3.3 Configure DNS

In your domain registrar (e.g., Namecheap):

1. Go to **DNS Settings**
2. Add a **CNAME** record:
   - Host: `chat`
   - Value: `<railway-provided-value>.up.railway.app`
   - TTL: Automatic

3. Wait 5-30 minutes for DNS propagation

### 3.4 SSL Certificate
Railway automatically provisions SSL certificates via Let's Encrypt. Your site will be `https://` automatically!

---

## 💰 Part 4: Cost Breakdown

### Railway.app Pricing (Estimated)

| Service | Cost/Month |
|---------|------------|
| Frontend | ~$0-5 (low traffic) |
| Backend | ~$5-10 |
| PostgreSQL | ~$5-7 |
| **Total** | **~$10-22/month** |

### API Costs (Estimated for MVP demo)

| API | Cost |
|-----|------|
| OpenAI (embeddings) | Already done (~$0.07 one-time) |
| Anthropic (Claude) | ~$1-5/month for demo traffic |

### Domain Cost
- ~$10-15/year

**Total MVP Cost: ~$15-30/month**

---

## 🔧 Part 5: Post-Deployment Tasks

### 5.1 Migrate Database

After PostgreSQL is running on Railway:

```bash
# Export local database
docker exec stirling_chat_db pg_dump -U postgres stirling_chat > backup.sql

# Import to Railway (get connection string from Railway)
psql "postgresql://user:pass@host:port/railway" < backup.sql
```

Or use Railway's built-in data import feature.

### 5.2 Test Everything

1. Open your deployed URL
2. Test chat functionality
3. Test feedback submission
4. Check lead capture works
5. Verify database is storing data

### 5.3 Monitor Logs

In Railway dashboard:
- Click on any service
- Go to **"Deployments"** tab
- Click **"View Logs"**

---

## 🆘 Troubleshooting

### Problem: "Application Error" on Railway
```
Check logs in Railway dashboard
Common causes:
- Missing environment variables
- Database connection issues
- Port configuration
```

### Problem: Frontend can't reach Backend
```
Ensure VITE_API_URL is set correctly
Should be the full Railway backend URL
```

### Problem: Database connection refused
```
Check DATABASE_URL format:
postgresql://user:password@host:port/database
```

### Problem: CORS errors
```
Update backend CORS settings to include Railway URLs:
CORS_ORIGINS=https://your-frontend.up.railway.app,https://chat.yourdomain.com
```

---

## 📋 Deployment Checklist

Before deploying:
- [ ] All code committed to GitHub
- [ ] `.env` is in `.gitignore`
- [ ] Backend Dockerfile created
- [ ] Environment variables documented
- [ ] Database backup created

After deploying:
- [ ] All services running (green status)
- [ ] Environment variables set
- [ ] Database migrated
- [ ] Custom domain configured (optional)
- [ ] SSL working (https://)
- [ ] Chat functionality tested
- [ ] Feedback system tested

---

## 🎯 Quick Start Summary

1. **Push to GitHub**
   ```bash
   git add . && git commit -m "Deploy" && git push
   ```

2. **Create Railway Project**
   - Connect GitHub repo
   - Add PostgreSQL database
   - Set environment variables

3. **Deploy**
   - Railway auto-deploys from GitHub

4. **Test**
   - Visit your Railway URL
   - Test all features

5. **Custom Domain** (Optional)
   - Buy domain
   - Add CNAME record
   - Configure in Railway

---

**Congratulations!** Your Stirling Chat MVP is now live! 🎉
