# 🚀 Railway.app Deployment Guide for Beginners

## Stirling University Chatbot - Complete Step-by-Step Tutorial

---

## 📚 What You're Going to Learn

This guide will teach you how to deploy your Stirling University Chatbot from your local computer to the internet using Railway.app.

**What this means:** Instead of only being able to use your chatbot on your computer, anyone with an internet link will be able to access it!

### What is Railway.app?

Think of Railway.app like a magical computer in the cloud that runs your code 24/7. You don't have to worry about:

- Buying servers
- Setting up databases
- Managing security certificates
- Keeping your computer on all the time

Railway handles all of that for you.

---

## 🏗️ Understanding Your Project Structure

Before we deploy, let's understand what you have:

```
stirling_chat/
├── backend/                 # Your Python API (the brain)
│   ├── main.py             # Main FastAPI application
│   ├── config.py           # Settings and configuration
│   ├── requirements.txt    # Python packages needed
│   └── models.py           # Data structures
├── frontend/               # Your React app (the face)
│   ├── src/                # React source code
│   ├── package.json        # Node.js packages needed
│   └── vite.config.js      # Build configuration
├── scripts/                # Helper scripts
│   ├── enhanced_rag.py     # AI chat logic
│   └── init_db.sql         # Database setup
└── docker-compose.yml      # Local development setup
```

**Simple Explanation:**

- **Backend**: The smart part that answers questions using AI
- **Frontend**: The pretty website interface that users see
- **Database**: Where all the university information is stored
- **Scripts**: Helper programs that make everything work

---

## 🎯 The Big Picture: What We're Doing

### Current Situation (Local Only)

```
Your Computer → Backend + Database + Frontend → Only you can use it
```

### After Deployment (Everyone Can Use)

```
User's Browser → Internet → Railway Cloud → Your App → Anyone can use it
```

---

## 📋 Preparation Checklist

Before we start, make sure you have:

### ✅ Required Accounts

1. **GitHub Account** - Free at [github.com](https://github.com)
2. **Railway.app Account** - Free at [railway.app](https://railway.app)
3. **API Keys** (you should already have these):
   - OpenAI API Key
   - Anthropic API Key
   - FireCrawl API Key

### ✅ Technical Requirements

1. Your code is pushed to GitHub
2. Your project works locally (you can test it on your computer)
3. You have your API keys ready

---

## 🚀 Phase 1: Prepare Your Backend for the Cloud

### Step 1: Create a Dockerfile for Your Backend

**What is a Dockerfile?**
Think of it like a recipe that tells Railway how to cook your application. It contains step-by-step instructions on how to set up everything needed to run your code.

**Why do we need it?**
Railway doesn't have Python, FastAPI, or your specific requirements pre-installed. The Dockerfile tells Railway exactly what to install and how to run your app.

**What to do:**
Create a new file called `Dockerfile` in your `backend` folder:

```dockerfile
# Start with Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies we need
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements first (for better caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code
COPY . .

# Create a non-root user (security best practice)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Tell Railway which port to use
EXPOSE 8000

# Health check so Railway knows if your app is working
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start your FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Save this file as:** `backend/Dockerfile`

**What each line does:**

- `FROM python:3.11-slim` - Start with a lightweight Python operating system
- `WORKDIR /app` - Create a folder called `/app` to work in
- `RUN apt-get update...` - Install system tools we need
- `COPY requirements.txt .` - Copy your Python requirements file
- `RUN pip install...` - Install all Python packages
- `COPY . .` - Copy all your code into the container
- `USER app` - Run as a regular user (safer than running as root)
- `EXPOSE 8000` - Tell Railway your app uses port 8000
- `HEALTHCHECK` - Tell Railway how to check if your app is healthy
- `CMD` - The command to start your application

---

### Step 2: Create Railway Configuration

**What is this?**
A configuration file that tells Railway how to deploy your service.

**Why do we need it?**
Railway needs to know specific settings like health check paths and restart policies.

**What to do:**
Create a new file called `railway.toml` in your `backend` folder:

```toml
[deploy]
# Health check endpoint
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10

[build]
# Use Docker to build
builder = "nixpacks"

[[services]]
name = "stirling-chat-backend"
source = "."
```

**Save this file as:** `backend/railway.toml`

---

### Step 3: Create Database Migration Script

**What is database migration?**
When you move from local to cloud, you need to set up your database structure in the cloud. This script automatically creates all the tables and extensions your database needs.

**Why do we need it?**
Railway gives you a fresh, empty database. We need to create the same structure you have locally.

**What to do:**
Create a new file called `migrate.py` in your `backend` folder:

```python
#!/usr/bin/env python3
"""
Database Migration Script for Railway.app
Sets up PostgreSQL with pgvector extension and tables
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Setup database with pgvector extension and schema"""
  
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
  
    try:
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
      
        print("📦 Installing pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
      
        print("🗃️ Creating tables...")
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_url TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                title TEXT NOT NULL,
                full_content TEXT NOT NULL,
                crawled_at TIMESTAMP DEFAULT NOW(),
                metadata JSONB
            );
        """)
      
        # Chunks table with vector support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536),
                token_count INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
      
        print("🔍 Creating indexes...")
        # Vector similarity index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
            ON chunks USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100);
        """)
      
        # Other useful indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks(document_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS documents_category_idx ON documents(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS documents_url_idx ON documents(source_url);")
      
        print("✅ Database setup complete!")
      
        cursor.close()
        conn.close()
        return True
      
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Railway database migration...")
    success = setup_database()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed - check logs above")
        exit(1)
```

**Save this file as:** `backend/migrate.py`

---

### Step 4: Update Configuration for Production

**Why do we need this?**
Your app needs to work differently in the cloud vs. on your computer. For example, it needs to accept connections from anywhere (not just localhost) and handle Railway's specific environment.

**What to do:**
Your `config.py` is already mostly set up correctly! Just make sure it has these settings:

```python
# In backend/config.py - make sure these lines exist:
HOST: str = "0.0.0.0"  # Accept connections from anywhere
PORT: int = 8000
DEBUG: bool = False     # Don't show debug info in production
```

---

## 🌐 Phase 2: Deploy Your Backend to Railway.app

### Step 5: Set Up Railway Account

**What to do:**

1. Go to [railway.app](https://railway.app)
2. Click "Sign Up with GitHub" (this is the easiest way)
3. Authorize Railway to access your GitHub account
4. Add a payment method (Railway requires this for databases, but you'll only pay a few dollars)

**Why GitHub?**
Using GitHub makes deployment automatic - when you push code changes, Railway can automatically redeploy your app.

### Step 6: Create Your First Railway Project

**What is a Railway Project?**
A project is like a folder that groups related services together. You'll have a backend service and a database service in the same project.

**What to do:**

1. In Railway dashboard, click "New Project"
2. Select "Deploy from GitHub repository"
3. Find your `stirling_chat` repository
4. Click "Deploy"

**What happens next?**
Railway will analyze your code and suggest deployment options.

### Step 7: Configure Your Backend Service

**What to do:**

1. Railway will show you detected services. Click on your backend service.
2. Go to the "Settings" tab
3. Add these environment variables:

```
DATABASE_URL=          # We'll fill this in Step 9
OPENAI_API_KEY=        # Your OpenAI API key
ANTHROPIC_API_KEY=     # Your Anthropic API key  
FIRECRAWL_API_KEY=     # Your FireCrawl API key
ENVIRONMENT=production
DEBUG=false
```

**Why environment variables?**
This keeps your secret API keys out of your code. If you share your code on GitHub, people won't see your keys.

### Step 8: Create Your PostgreSQL Database

**What to do:**

1. In your Railway project, click "+ New"
2. Select "PostgreSQL" from the database section
3. Choose the standard PostgreSQL (pgvector will be added via our migration script)
4. Click "Add PostgreSQL"

**Why Railway PostgreSQL?**

- Automatic backups
- Managed security updates
- No server maintenance
- Easy connection strings

### Step 9: Connect Backend to Database

**What to do:**

1. Click on your new PostgreSQL service
2. Go to the "Connect" tab
3. Copy the "DATABASE_URL" (it looks like: `postgresql://username:password@host:port/database`)
4. Go back to your backend service settings
5. Paste this URL as the DATABASE_URL environment variable

**Why this step?**
Your backend needs to know where to find the database in the cloud.

### Step 10: Run Database Migration

**What to do:**

1. Go to your backend service in Railway
2. Click the "Logs" tab to see what's happening
3. Click "Restart" to trigger a new deployment
4. Wait for the deployment to finish
5. Click the "Console" tab
6. Run this command: `python migrate.py`

**What you should see:**

```
🚀 Starting Railway database migration...
🔌 Connecting to PostgreSQL...
📦 Installing pgvector extension...
🗃️ Creating tables...
🔍 Creating indexes...
✅ Database setup complete!
🎉 Migration completed successfully!
```

**Why this step?**
This creates all the database tables your app needs to store university information.

### Step 11: Test Your Backend

**What to do:**

1. Find your backend URL (click on your backend service, copy the URL shown)
2. Open this URL in your browser: `https://your-backend-name.railway.app/health`
3. You should see something like: `{"status": "healthy", "timestamp": "..."}`

**Why test the health endpoint?**
This is the simplest way to verify your backend is running correctly before adding complexity.

---

## 🎨 Phase 3: Prepare Your Frontend for Production

### Step 12: Create Production Frontend Dockerfile

**Why do we need a different Dockerfile?**
Your current frontend Dockerfile runs in development mode. For production, we need to build the app and serve it as static files.

**What to do:**
Create a new file called `Dockerfile.prod` in your `frontend` folder:

```dockerfile
# Build stage - create the production build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Production stage - serve the built files
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx web server
CMD ["nginx", "-g", "daemon off;"]
```

**Save this file as:** `frontend/Dockerfile.prod`

### Step 13: Create Nginx Configuration

**What is Nginx?**
Nginx is a web server that will serve your React app to users. It's very fast and efficient.

**Why do we need it?**
Instead of running a Node.js server (which uses more memory), we'll use Nginx to serve static HTML/CSS/JS files.

**What to do:**
Create a new file called `nginx.conf` in your `frontend` folder:

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
  
    sendfile        on;
    keepalive_timeout  65;
  
    # Gzip compression (makes your site faster)
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
  
    server {
        listen       80;
        server_name  localhost;
        root         /usr/share/nginx/html;
        index        index.html;
      
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
      
        # Handle React Router (refreshes work correctly)
        location / {
            try_files $uri $uri/ /index.html;
        }
      
        # Cache static assets for 1 year
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
      
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

**Save this file as:** `frontend/nginx.conf`

### Step 14: Create Frontend Railway Configuration

**What to do:**
Create a new file called `railway.toml` in your `frontend` folder:

```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10

[build]
builder = "nixpacks"

[[services]]
name = "stirling-chat-frontend"
source = "."
```

**Save this file as:** `frontend/railway.toml`

---

## 🌐 Phase 4: Deploy Your Frontend

### Step 15: Deploy Frontend Service

**What to do:**

1. In your Railway project, click "+ New"
2. Select "GitHub Repo" and choose the same repository
3. Railway will ask which directory to deploy from - select "frontend"
4. Click "Deploy"

**Why separate services?**
This allows you to update the frontend without affecting the backend, and vice versa.

### Step 16: Connect Frontend to Backend

**What to do:**

1. Click on your new frontend service
2. Go to "Settings" tab
3. Add this environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend-name.railway.app
   ```

   (Replace `your-backend-name` with your actual backend service name)

**Why this step?**
Your frontend needs to know where to send API requests. In development, it used `localhost:8000`, but in production it needs your Railway backend URL.

### Step 17: Test Your Full Application

**What to do:**

1. Find your frontend URL (click on your frontend service)
2. Open it in your browser
3. Try asking a question like "What are the entry requirements for Computer Science?"
4. You should get a helpful answer with sources

**What if it doesn't work?**

- Check the logs in both frontend and backend services
- Make sure the VITE_API_BASE_URL is correct
- Verify your API keys are set correctly

---

## 🔒 Phase 5: Production Safeguards

### Step 18: Set Up Rate Limiting

**Why?**
To prevent people from abusing your API and running up huge bills.

**What to do:**
Add rate limiting to your backend. Create a file called `rate_limit.py` in your `backend` folder:

```python
import time
from collections import defaultdict
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting - allows 60 requests per minute per IP"""
  
    def __init__(self, app, calls=60, period=60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
  
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
      
        # Clean old requests
        now = time.time()
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]
      
        # Check if rate limit exceeded
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
      
        # Add current request
        self.clients[client_ip].append(now)
      
        # Process request
        response = await call_next(request)
        return response
```

Then add this to your `main.py`:

```python
# Add near the top of main.py
from rate_limit import RateLimitMiddleware

# Add after app = FastAPI(...)
app.add_middleware(RateLimitMiddleware, calls=60, period=60)
```

### Step 19: Set Up Database Backups

**What to do:**

1. Go to your PostgreSQL service in Railway
2. Click "Settings"
3. Enable "Automatic Backups" if available
4. Set retention to 7 days

**Why?**
If something goes wrong, you can restore your data from a backup.

### Step 20: Monitor Your Costs

**What to watch:**

- Railway usage (in Railway dashboard)
- API costs (OpenAI, Anthropic, FireCrawl dashboards)
- Database storage usage

**Set alerts:**

- Railway spending alerts
- API usage alerts

---

## 🎯 Phase 6: Testing and Going Live

### Step 21: Full Testing Checklist

**Test these scenarios:**

- [ ] Basic chat: "What are entry requirements?"
- [ ] Complex question: "Compare Computer Science vs Software Engineering"
- [ ] Sources appear correctly
- [ ] No error messages in console
- [ ] Fast response times (under 10 seconds)
- [ ] Mobile works (try on your phone)

### Step 22: Optional - Custom Domain

**Why?**
Instead of `your-app.railway.app`, you can use `yourapp.com`.

**What to do:**

1. Buy a domain (optional, costs ~$15/year)
2. In Railway, go to project settings
3. Click "Domains" and add your domain
4. Follow the DNS instructions

### Step 23: Share Your App!

**What to do:**

- Share the URL with friends
- Test with real users
- Collect feedback
- Monitor costs and performance

---

## 🆘 Troubleshooting Guide

### Common Problems and Solutions

**Problem: Backend shows "Application Error"**

- Check the logs in Railway
- Make sure all environment variables are set
- Verify the migration ran successfully

**Problem: Frontend can't connect to backend**

- Check VITE_API_BASE_URL is correct
- Make sure backend is running
- Check CORS settings in backend

**Problem: Database connection failed**

- Verify DATABASE_URL is correct
- Make sure PostgreSQL service is running
- Check if migration was successful

**Problem: High costs**

- Monitor API usage
- Implement caching
- Consider rate limiting

**Problem: Slow responses**

- Check database query performance
- Monitor response times in logs
- Consider upgrading Railway plan

---

## 📈 What You've Accomplished

**Technical Skills Learned:**

- Docker containerization
- Environment variable management
- Database migrations
- Production deployment
- Rate limiting and security
- Cost monitoring

**Infrastructure Understanding:**

- How cloud hosting works
- Database management
- API security
- Performance optimization

**DevOps Practices:**

- Configuration management
- Health checks
- Logging and monitoring
- Backup strategies

---

## 🎉 Congratulations!

You now have a fully deployed, production-ready chatbot that anyone in the world can use!

**What's next:**

- Monitor your usage and costs
- Collect user feedback
- Add new features
- Scale as needed

**Remember:** The key to successful deployment is taking it step by step, testing each component, and monitoring everything once it's live.

Happy deploying! 🚀
