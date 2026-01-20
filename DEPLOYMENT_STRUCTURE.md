# 🚀 Stirling Chat - Deployment Structure Documentation

## 📁 Project Organization

This project is professionally organized with **separate configurations** for:
- **Local Development** (Docker Compose)
- **Railway.app Production Deployment**

---

## 🏗️ File Structure Overview

### **Backend Files**

#### Local Development:
- `backend/Dockerfile` - Local development container (with hot reload)
- `backend/requirements.txt` - Python dependencies
- `.env` - Local environment variables

#### Railway Deployment:
- `backend/Dockerfile.railway` ⭐ **RAILWAY PRODUCTION**
- `backend/railway.toml` - Railway deployment configuration
- `backend/migrate.py` - Database migration script for Railway
- `backend/config.py` - Environment-aware configuration (supports Railway PORT env var)

### **Frontend Files**

#### Local Development:
- `frontend/Dockerfile` - Local development container (Vite dev server)
- `frontend/docker-compose.yml` - Local frontend service
- `frontend/.env` - Local environment variables

#### Railway Deployment:
- `frontend/Dockerfile.railway` ⭐ **RAILWAY PRODUCTION**
- `frontend/Dockerfile.prod` - Same as Dockerfile.railway (kept for compatibility)
- `frontend/railway.toml` - Railway deployment configuration
- `frontend/nginx.conf` - Production web server configuration

### **Database Files**

#### Local Development:
- `docker-compose.yml` - PostgreSQL with pgvector (port 5433)
- `scripts/init_db.sql` - Local database initialization

#### Railway Deployment:
- `backend/migrate.py` - Creates all tables and indexes on Railway PostgreSQL

---

## ✅ Railway Deployment Files Checklist

### **Backend (Ready ✅)**

| File | Status | Purpose |
|------|--------|---------|
| `backend/Dockerfile.railway` | ✅ Ready | Production Docker build |
| `backend/railway.toml` | ✅ Ready | Railway configuration |
| `backend/migrate.py` | ✅ Ready | Database setup script |
| `backend/config.py` | ✅ Ready | Environment variables handler |
| `backend/main.py` | ✅ Ready | FastAPI application with `/health` endpoint |

**Backend Features:**
- ✅ Multi-stage build with security (non-root user)
- ✅ Health check endpoint at `/health`
- ✅ Dynamic PORT binding from Railway environment
- ✅ PostgreSQL connection with pgvector support
- ✅ Complete database migration script (13 tables + 30+ indexes)
- ✅ Lead capture system with tracking
- ✅ Rate limiting functionality
- ✅ Safety incident monitoring

### **Frontend (Ready ✅)**

| File | Status | Purpose |
|------|--------|---------|
| `frontend/Dockerfile.railway` | ✅ Ready | Production Docker build |
| `frontend/railway.toml` | ✅ Ready | Railway configuration |
| `frontend/nginx.conf` | ✅ Ready | Web server configuration |
| `frontend/vite.config.js` | ✅ Ready | Build configuration |

**Frontend Features:**
- ✅ Multi-stage build (Node builder + Nginx server)
- ✅ Optimized production build with code splitting
- ✅ Gzip compression enabled
- ✅ Security headers configured
- ✅ React Router support (SPA routing)
- ✅ Health check endpoint at `/health`
- ✅ Static asset caching (1 year)

---

## 🔧 Configuration Details

### **Backend Configuration (`backend/config.py`)**

```python
# Key Railway-compatible settings:
HOST: str = "0.0.0.0"  # Accept connections from anywhere
PORT: int = int(os.environ.get("PORT", 8000))  # Railway dynamic port
DATABASE_URL: str  # From Railway PostgreSQL service
CORS_ORIGINS: str  # Will be set to Railway frontend URL
```

### **Backend Railway Config (`backend/railway.toml`)**

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.railway"  # Uses Railway-specific Dockerfile

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### **Frontend Railway Config (`frontend/railway.toml`)**

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.railway"  # Uses Railway-specific Dockerfile

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

---

## 🗄️ Database Migration Script

**File:** `backend/migrate.py`

**Creates the following tables (13 total):**
1. ✅ `documents` - Scraped university content
2. ✅ `chunks` - Text chunks with vector embeddings (1536 dimensions)
3. ✅ `conversations` - User chat sessions
4. ✅ `messages` - Individual chat messages with intent tracking
5. ✅ `conversation_feedback` - User feedback ratings
6. ✅ `safety_incidents` - Safety monitoring logs
7. ✅ `conversation_context` - Conversation context tracking
8. ✅ `leads` - Lead/contact information capture
9. ✅ `lead_capture_tracking` - Lead capture progress tracking
10. ✅ `phone_country_codes` - Phone number validation lookup
11. ✅ `rate_limit_tracking` - API rate limiting
12. ✅ `schema_version` - Database schema versioning

**Creates the following indexes (30+ total):**
- ✅ Vector similarity index (IVFFlat for fast semantic search)
- ✅ Document category and URL indexes
- ✅ Conversation and message indexes (with intent tracking)
- ✅ Feedback and safety incident indexes
- ✅ Lead capture and tracking indexes
- ✅ Rate limiting indexes
- ✅ Conversation context indexes

---

## 📋 Railway Deployment Checklist

### **Prerequisites:**
- [ ] GitHub repository is up to date
- [ ] Railway.app account created
- [ ] API keys ready (OpenAI, Anthropic)

### **Step 1: Database (Deploy First)**
- [ ] Create PostgreSQL service in Railway
- [ ] Copy `DATABASE_URL` from Railway dashboard
- [ ] Verify PostgreSQL is running

### **Step 2: Backend (Deploy Second)**
- [ ] Deploy from GitHub repo (root directory: `backend`)
- [ ] Set environment variables:
  - `DATABASE_URL=${POSTGRES_URL}` (reference from PostgreSQL service)
  - `OPENAI_API_KEY=<your-key>`
  - `ANTHROPIC_API_KEY=<your-key>`
  - `CORS_ORIGINS=*` (or specific frontend URL)
  - `ENVIRONMENT=production`
- [ ] Wait for deployment to complete
- [ ] Run migration: `python migrate.py` (via Railway console or custom start command)
- [ ] Test health endpoint: `https://your-backend.railway.app/health`
- [ ] Copy backend URL for frontend

### **Step 3: Frontend (Deploy Last)**
- [ ] Deploy from GitHub repo (root directory: `frontend`)
- [ ] Set environment variable:
  - `VITE_API_BASE_URL=<backend-url-from-step-2>`
- [ ] Wait for deployment to complete
- [ ] Test health endpoint: `https://your-frontend.railway.app/health`
- [ ] Test full application

---

## 🔐 Environment Variables Reference

### **Backend Required Variables:**
```bash
DATABASE_URL=postgresql://user:pass@host:port/db  # From Railway PostgreSQL
OPENAI_API_KEY=sk-...                              # Your OpenAI key
ANTHROPIC_API_KEY=sk-ant-...                       # Your Anthropic key
CORS_ORIGINS=*                                     # Or specific frontend URL
ENVIRONMENT=production                             # Set to production
```

### **Frontend Required Variables:**
```bash
VITE_API_BASE_URL=https://your-backend.railway.app  # Backend URL from Railway
```

---

## 🚨 Important Notes

### **File Naming Convention:**
- `Dockerfile` = Local development only
- `Dockerfile.railway` = Railway production deployment
- `docker-compose.yml` = Local development only
- `railway.toml` = Railway deployment configuration

### **Port Configuration:**
- **Local Backend:** Port 8001 (configured in local .env)
- **Railway Backend:** Dynamic port from `$PORT` environment variable
- **Local Frontend:** Port 3000
- **Railway Frontend:** Port 80 (Nginx default)

### **Database Differences:**
- **Local:** PostgreSQL on port 5433 (Docker Compose)
- **Railway:** Managed PostgreSQL with automatic backups

### **Build Process:**
- **Local:** Development mode with hot reload
- **Railway:** Production build with optimizations and security hardening

---

## ✅ Verification Commands

### **After Backend Deployment:**
```bash
# Check health
curl https://your-backend.railway.app/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2026-01-20T...",
  "version": "1.0",
  "database_connected": true
}
```

### **After Frontend Deployment:**
```bash
# Check health
curl https://your-frontend.railway.app/health

# Expected response:
healthy
```

### **After Migration:**
```bash
# Check database tables (via Railway PostgreSQL console)
\dt

# Expected tables:
documents, chunks, conversations, messages, feedback, safety_incidents
```

---

## 🎯 Deployment Order (Critical)

**ALWAYS deploy in this order:**

1. **PostgreSQL Database** (First)
2. **Backend API** (Second - needs database)
3. **Run Migration** (Before frontend)
4. **Frontend** (Last - needs backend URL)

**Why this order?**
- Backend needs database connection to start
- Migration needs backend environment to run
- Frontend needs backend URL to make API calls

---

## 📊 Current Status

### **Local Development:**
- ✅ Backend running on port 8001
- ✅ Frontend running on port 3000 (Docker)
- ✅ PostgreSQL running on port 5433 (Docker)

### **Railway Deployment:**
- ✅ All deployment files created and configured
- ✅ Dockerfiles optimized for production
- ✅ Railway.toml configurations ready
- ✅ Database migration script complete
- ✅ Environment variable handling configured
- ⏳ Ready to deploy (waiting for user to push to GitHub)

---

## 🔄 Next Steps

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Deploy to Railway** following the deployment order above

3. **Monitor deployment** via Railway dashboard logs

4. **Test application** using the provided verification commands

---

**Last Updated:** January 20, 2026
**Status:** All deployment files ready for Railway.app deployment
