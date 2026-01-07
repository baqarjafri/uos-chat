# Stirling University AI Chatbot

> An intelligent conversational AI chatbot for prospective students at the University of Stirling.

![Status](https://img.shields.io/badge/Status-MVP%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+-61DAFB)

---

## Overview

This chatbot helps prospective students explore courses, understand entry requirements, learn about fees, and get answers about studying at the University of Stirling. It uses a Retrieval-Augmented Generation (RAG) system powered by Claude AI.

### Key Features

- **Conversational AI** - Natural language understanding with context memory
- **RAG System** - Hybrid search (vector + keyword) with re-ranking
- **Lead Capture** - Progressive data collection for admissions follow-up
- **Guardrails** - Topic boundaries, safety filters, prompt injection prevention
- **Feedback System** - 3-level rating with suggestions for improvement
- **Responsive UI** - Modern chat widget with fullscreen mode

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- API Keys: OpenAI, Anthropic

### Step 1: Start Database

```bash
docker-compose up -d
```

Verify it's running:
```bash
docker ps
# Should show: stirling_chat_db on port 5433
```

### Step 2: Start Backend

```bash
# Activate virtual environment
venv\Scripts\activate

# Start FastAPI server
cd backend
python main.py
```

Expected output:
```
[OK] FastAPI backend started successfully!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Frontend

Open a **new terminal**:

```bash
cd frontend
docker-compose up -d
```

Or without Docker:
```bash
cd frontend
npm install
npm run dev
```

### Step 4: Access Application

| Service | URL |
|---------|-----|
| **Chat Widget** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **API Health** | http://localhost:8000/health |

---

## Project Structure

```
stirling_chat/
├── backend/                    # FastAPI REST API
│   ├── main.py                 # API endpoints (7 routes)
│   ├── models.py               # Pydantic request/response models
│   ├── config.py               # Environment configuration
│   └── .env                    # API keys (not in git)
│
├── frontend/                   # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget.jsx  # Main chat component
│   │   │   └── FeedbackModal.jsx
│   │   └── App.jsx
│   └── Dockerfile
│
├── scripts/                    # Core RAG System
│   ├── conversational_system.py  # LangGraph 3-agent system
│   ├── enhanced_rag.py           # Hybrid search + re-ranking
│   ├── guardrails.py             # Safety & topic boundaries
│   ├── lead_manager.py           # Progressive lead capture
│   ├── feedback_system.py        # Rating & suggestions
│   ├── scrape_to_db.py           # FireCrawl web scraper
│   ├── process_chunks.py         # Text chunking
│   ├── generate_embeddings.py    # OpenAI embeddings
│   └── rescrape_with_js.py       # JS-rendered re-scraper
│
├── database/                   # SQL Schemas
│   ├── schema_conversations.sql  # Main database schema
│   └── migration_lead_management_v2.sql
│
├── data/urls/                  # Scraped URL lists by category
│
├── docker-compose.yml          # PostgreSQL + pgvector
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, TailwindCSS, Lucide Icons |
| **Backend** | FastAPI, Python 3.11, Pydantic |
| **Database** | PostgreSQL 16 + pgvector extension |
| **LLM** | Claude 3 Haiku (Anthropic) |
| **Embeddings** | OpenAI text-embedding-3-small (1536 dims) |
| **Orchestration** | LangGraph (3-agent state machine) |
| **Scraping** | FireCrawl API with JS rendering |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send message, get AI response |
| `GET` | `/conversation/{session_id}` | Get conversation history |
| `POST` | `/conversation/{session_id}/end` | End conversation |
| `POST` | `/feedback` | Submit feedback rating |
| `GET` | `/feedback/stats` | Get feedback statistics |
| `GET` | `/feedback/bad` | List bad feedback for review |
| `GET` | `/health` | Health check |

Full API documentation: http://localhost:8000/docs

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
# Database (Docker container on port 5433)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/stirling_chat

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional
FIRECRAWL_API_KEY=fc-...  # For re-scraping
```

**Important:** Port is `5433` (not `5432`) to avoid conflicts with local PostgreSQL.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│                   React Chat Widget                         │
│                    (localhost:3000)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────┐
│                     FASTAPI BACKEND                         │
│                    (localhost:8000)                         │
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
│  │  (1,206)    │  │  (15,000+)  │  │   + messages        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Backend won't start

```bash
# Reinstall dependencies
venv\Scripts\activate
pip install -r requirements.txt
```

### Database connection error

```bash
# Check if container is running
docker ps

# Start if not running
docker-compose up -d

# Verify port 5433
docker logs stirling_chat_db
```

### Frontend won't load

```bash
# Restart frontend container
docker restart stirling_frontend

# Or rebuild
cd frontend
docker-compose down
docker-compose up -d --build
```

### CORS errors

Check `backend/.env` has correct CORS origins:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Development

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

SQL schemas are in `database/` folder. Apply with:
```bash
docker exec -i stirling_chat_db psql -U postgres -d stirling_chat < database/schema_conversations.sql
```

### Re-scraping Content

To update content with JS rendering:
```bash
python scripts/rescrape_with_js.py --category courses --limit 10
```

---

## Deployment

See `tutorials/TUTORIAL_DEPLOYMENT.md` for Railway.app deployment guide.

**Estimated costs:**
- Railway hosting: ~$10-20/month
- Anthropic API: ~$1-5/month (demo traffic)
- OpenAI API: ~$0.07 one-time (embeddings done)

---

## License

Private - University of Stirling

---

## Contact

For questions about this project, contact the development team.
