# 🎓 Stirling University AI Chatbot

> An intelligent conversational AI chatbot for prospective students at the University of Stirling, powered by Claude AI and RAG technology.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791)

---

## 📋 Overview

This chatbot helps prospective students explore courses, understand entry requirements, learn about fees, and get answers about studying at the University of Stirling. It uses a Retrieval-Augmented Generation (RAG) system powered by Claude 3 Haiku with advanced lead capture and safety features.

### ✨ Key Features

- **🤖 Conversational AI** - Natural language understanding with context memory
- **🔍 Advanced RAG System** - Hybrid search (vector + keyword) with re-ranking
- **📊 Lead Capture** - Progressive data collection with tracking
- **🛡️ Safety Guardrails** - Topic boundaries, safety filters, prompt injection prevention
- **⭐ Feedback System** - 3-level rating with suggestions for improvement
- **📱 Responsive UI** - Modern chat widget with fullscreen mode
- **🚀 Production Ready** - Railway.app deployment configured

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker Desktop**
- **API Keys:** OpenAI (embeddings), Anthropic (Claude)

### Step 1: Clone & Setup Environment

```bash
# Clone repository
git clone https://github.com/baqarjafri/uos-chat.git
cd uos-chat

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
```

### Step 2: Start Database

```bash
# Start PostgreSQL with pgvector
docker-compose up -d

# Verify it's running
docker ps
# Should show: stirling_chat_db on port 5433
```

### Step 3: Install Dependencies & Start Backend

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
cd backend
python main.py
```

**Expected output:**
```
[OK] FastAPI backend started successfully!
[DB] Database: Connected
[RAG] RAG System: Initialized
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 4: Start Frontend

**Option A: Using Docker (Recommended)**
```bash
cd frontend
docker-compose up -d
```

**Option B: Using npm**
```bash
cd frontend
npm install
npm run dev
```

### Step 5: Access Application

| Service | URL | Description |
|---------|-----|-------------|
| **Chat Widget** | http://localhost:3000 | Main chat interface |
| **API Documentation** | http://localhost:8001/docs | Interactive API docs |
| **API Health Check** | http://localhost:8001/health | Backend status |
| **Database** | localhost:5433 | PostgreSQL + pgvector |

---

## 📁 Project Structure

```
stirling_chat/
├── backend/                           # FastAPI REST API
│   ├── main.py                        # API endpoints (7 routes)
│   ├── models.py                      # Pydantic request/response models
│   ├── config.py                      # Environment configuration
│   ├── Dockerfile                     # Local development
│   ├── Dockerfile.railway             # Railway production deployment
│   ├── railway.toml                   # Railway configuration
│   ├── migrate.py                     # Database migration (13 tables)
│   └── requirements.txt               # Backend dependencies
│
├── frontend/                          # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget.jsx         # Main chat component
│   │   │   ├── FeedbackModal.jsx      # Feedback collection
│   │   │   └── DisclaimerModal.jsx    # Initial disclaimer
│   │   ├── config.js                  # API configuration
│   │   └── App.jsx                    # Root component
│   ├── Dockerfile                     # Local development
│   ├── Dockerfile.railway             # Railway production deployment
│   ├── railway.toml                   # Railway configuration
│   ├── nginx.conf                     # Production web server config
│   └── package.json                   # Frontend dependencies
│
├── scripts/                           # Core RAG & AI System
│   ├── conversational_system.py       # LangGraph 3-agent system
│   ├── enhanced_rag.py                # Hybrid search + re-ranking
│   ├── guardrails.py                  # Safety & topic boundaries
│   ├── lead_manager.py                # Progressive lead capture
│   ├── feedback_system.py             # Rating & suggestions
│   ├── scrape_to_db.py                # FireCrawl web scraper
│   ├── process_chunks.py              # Text chunking
│   ├── generate_embeddings.py         # OpenAI embeddings
│   └── rescrape_with_js.py            # JS-rendered re-scraper
│
├── database/                          # SQL Schemas (legacy)
│   ├── schema_conversations.sql       # Original schema
│   └── migration_lead_management_v2.sql
│
├── data/urls/                         # Scraped URL lists by category
│
├── docker-compose.yml                 # PostgreSQL + pgvector (local)
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── DEPLOYMENT_STRUCTURE.md            # Deployment file organization
├── PRE_DEPLOYMENT_CHECKLIST.md        # Railway deployment guide
└── README.md                          # This file
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18, Vite, TailwindCSS | Modern, responsive UI |
| **Icons** | Lucide React | Beautiful icon library |
| **Backend** | FastAPI, Python 3.11 | High-performance REST API |
| **Database** | PostgreSQL 16 + pgvector | Vector similarity search |
| **LLM** | Claude 3 Haiku (Anthropic) | Conversational AI |
| **Embeddings** | OpenAI text-embedding-3-small | 1536-dimensional vectors |
| **Orchestration** | LangGraph | 3-agent state machine |
| **Scraping** | FireCrawl API | JS-rendered web scraping |
| **Deployment** | Railway.app | Production hosting |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send message, get AI response with sources |
| `GET` | `/conversation/{session_id}` | Get full conversation history |
| `POST` | `/conversation/{session_id}/end` | End conversation session |
| `POST` | `/feedback` | Submit feedback rating (good/average/bad) |
| `GET` | `/feedback/stats` | Get feedback statistics |
| `GET` | `/feedback/bad` | List bad feedback for review |
| `GET` | `/health` | Health check with database status |

**Full interactive documentation:** http://localhost:8001/docs

---

## ⚙️ Configuration

### Port Configuration

| Service | Local Port | Production |
|---------|-----------|------------|
| **Backend API** | 8001 | Dynamic (Railway $PORT) |
| **Frontend** | 3000 | 80 (Nginx) |
| **PostgreSQL** | 5433 | Railway managed |

**Note:** Backend uses port **8001** (not 8000) to avoid conflicts.

### Environment Variables

**Root `.env` file:**
```bash
# Database (local development)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/stirling_chat

# API Keys
OPENAI_API_KEY=sk-...                    # For embeddings
ANTHROPIC_API_KEY=sk-ant-...             # For Claude AI
FIRECRAWL_API_KEY=fc-...                 # Optional: for re-scraping

# Application Settings
ENVIRONMENT=development
API_HOST=localhost
API_PORT=8001                            # Backend runs on 8001
LOG_LEVEL=INFO

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# RAG Configuration
LLM_MODEL=claude-3-haiku-20240307
TOP_K_CHUNKS=5
MAX_RESPONSE_TOKENS=1024
LLM_TEMPERATURE=0.7
```

**Frontend `.env` file:**
```bash
VITE_API_BASE_URL=http://localhost:8001  # Points to backend
```

---

## 🗄️ Database Schema

The database includes **13 tables** for comprehensive functionality:

### Core RAG System
1. **documents** - Scraped university content (1,206 pages)
2. **chunks** - Text chunks with vector embeddings (15,000+)
3. **conversations** - Chat sessions with metadata
4. **messages** - Individual messages with intent tracking

### Advanced Features
5. **conversation_feedback** - User ratings and suggestions
6. **safety_incidents** - Safety monitoring logs
7. **conversation_context** - Context tracking
8. **leads** - Contact information capture
9. **lead_capture_tracking** - Lead progress tracking
10. **phone_country_codes** - Phone validation lookup
11. **rate_limit_tracking** - API rate limiting
12. **schema_version** - Database versioning

**Plus 30+ indexes** for optimal query performance.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                   React Chat Widget                         │
│                    (localhost:3000)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────┐
│                     FASTAPI BACKEND                         │
│                    (localhost:8001)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LANGGRAPH STATE MACHINE                │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │   │
│  │  │  ROUTER   │─▶│    RAG    │─▶│ LEAD CAPTURE  │   │   │
│  │  │  AGENT    │  │   AGENT   │  │    AGENT      │   │   │
│  │  └───────────┘  └───────────┘  └───────────────┘   │   │
│  │       │              │                              │   │
│  │       ▼              ▼                              │   │
│  │  ┌───────────┐  ┌───────────┐                      │   │
│  │  │GUARDRAILS │  │  HYBRID   │                      │   │
│  │  │  SYSTEM   │  │  SEARCH   │                      │   │
│  │  └───────────┘  └───────────┘                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQL
┌─────────────────────────▼───────────────────────────────────┐
│                    POSTGRESQL + PGVECTOR                    │
│                    (localhost:5433)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  documents  │  │   chunks    │  │   conversations     │ │
│  │  (1,206)    │  │  (15,000+)  │  │   + 10 more tables  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# Check .env file exists
ls .env
```

### Database connection error

```bash
# Check if container is running
docker ps

# Start if not running
docker-compose up -d

# Check logs
docker logs stirling_chat_db

# Verify port 5433 is available
netstat -an | findstr 5433
```

### Frontend won't load

```bash
# Check if backend is running first
curl http://localhost:8001/health

# Restart frontend container
docker restart stirling_frontend

# Or rebuild
cd frontend
docker-compose down
docker-compose up -d --build
```

### CORS errors

Check backend `.env` has correct CORS origins:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

For Railway deployment, set to `*` or specific Railway frontend URL.

### Port already in use

```bash
# Backend (8001)
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Frontend (3000)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## 🚀 Deployment to Railway.app

### Prerequisites
- Railway.app account
- GitHub repository connected
- API keys ready

### Deployment Order (Critical)

1. **PostgreSQL Database** (First)
2. **Backend API** (Second)
3. **Run Migration** (Before Frontend)
4. **Frontend** (Last)

### Quick Deployment Guide

**Step 1: PostgreSQL**
```
Railway → New → Database → PostgreSQL
Wait for provisioning
Copy DATABASE_URL
```

**Step 2: Backend**
```
Railway → New → GitHub Repo → baqarjafri/uos-chat
Root Directory: backend
Environment Variables:
  DATABASE_URL=${POSTGRES_URL}
  OPENAI_API_KEY=<your-key>
  ANTHROPIC_API_KEY=<your-key>
  CORS_ORIGINS=*
  ENVIRONMENT=production
```

**Step 3: Migration**
```
Backend Service → Settings → Deploy
Custom Start Command:
  python migrate.py && uvicorn main:app --host 0.0.0.0 --port $PORT
Redeploy
```

**Step 4: Frontend**
```
Railway → New → Same repo
Root Directory: frontend
Environment Variable:
  VITE_API_BASE_URL=<backend-url-from-step-2>
```

**Complete deployment guide:** See `PRE_DEPLOYMENT_CHECKLIST.md`

---

## 💰 Cost Estimates

### Development (Local)
- **Free** - All local resources

### Production (Railway.app)
- **Railway Hosting:** $5-15/month
  - Hobby Plan: $5/month (includes $5 credit)
  - PostgreSQL: ~$5-10/month
  - Backend + Frontend: Included
- **API Costs:**
  - OpenAI (embeddings): ~$0.02 per 1000 queries
  - Anthropic (Claude): ~$0.25 per 1000 queries
  - Estimated: $10-30/month for moderate usage

**Total:** ~$15-45/month for production deployment

---

## 🔧 Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

The migration script (`backend/migrate.py`) creates all 13 tables automatically. For Railway:

```bash
python backend/migrate.py
```

For local development, tables are created on first run.

### Re-scraping Content

To update content with JS rendering:

```bash
python scripts/rescrape_with_js.py --category courses --limit 10
```

### Code Quality

```bash
# Backend linting
cd backend
pylint *.py

# Frontend linting
cd frontend
npm run lint
```

---

## 📊 Project Statistics

- **University Pages Scraped:** 1,206
- **Text Chunks Generated:** 15,000+
- **Vector Dimensions:** 1,536
- **Database Tables:** 13
- **Database Indexes:** 30+
- **API Endpoints:** 7
- **Lines of Code:** ~5,000+

---

## 🔐 Security Features

- **Input Validation** - Pydantic models for all requests
- **SQL Injection Prevention** - Parameterized queries
- **Prompt Injection Detection** - Guardrails system
- **Rate Limiting** - Per-session and IP-based
- **CORS Configuration** - Restricted origins
- **Safety Monitoring** - Incident logging
- **Data Privacy** - Lead data encryption ready

---

## 📚 Documentation

- **API Documentation:** http://localhost:8001/docs (when running)
- **Deployment Guide:** `PRE_DEPLOYMENT_CHECKLIST.md`
- **File Structure:** `DEPLOYMENT_STRUCTURE.md`
- **Railway Guide:** `RAILWAY_DEPLOYMENT_GUIDE.md`

---

## 🤝 Contributing

This is a private project for the University of Stirling. For questions or contributions, contact the development team.

---

## 📝 License

Private - University of Stirling

---

## 📧 Contact

For questions about this project, contact the development team at the University of Stirling.

---

## 🎯 Project Status

- ✅ **Core RAG System** - Complete
- ✅ **Lead Capture** - Complete with tracking
- ✅ **Safety Guardrails** - Complete
- ✅ **Feedback System** - Complete
- ✅ **Railway Deployment** - Configured and ready
- ✅ **Production Ready** - All systems operational

---

**Last Updated:** January 20, 2026
**Version:** 1.0.0
**Repository:** https://github.com/baqarjafri/uos-chat
