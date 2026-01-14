# Stirling Chat - Complete Education Guide

## Welcome to the Codebase

This guide will teach you the entire Stirling University AI Chatbot codebase from the ground up. By the end, you'll understand every component, how they connect, and how data flows through the system.

---

## 📚 Guide Structure

| Part | File | What You'll Learn |
|------|------|-------------------|
| **1** | `01_PROJECT_OVERVIEW.md` | Project objectives, architecture, folder structure |
| **2** | `02_DATABASE_AND_DOCKER.md` | PostgreSQL, pgvector, Docker setup, schema design |
| **3** | `03_BACKEND_API.md` | FastAPI endpoints, request/response flow, configuration |
| **4** | `04_RAG_SYSTEM.md` | The AI brain: search, embeddings, Claude integration |
| **5** | `05_FRONTEND_UI.md` | React components, state management, user experience |

---

## 🎯 Project Objective

Build an **AI-powered admissions chatbot** for the University of Stirling that:

1. **Answers questions** about courses, fees, requirements, and campus life
2. **Uses RAG** (Retrieval-Augmented Generation) to provide accurate, sourced answers
3. **Captures leads** for the admissions team when queries need human follow-up
4. **Maintains guardrails** to stay on-topic and handle inappropriate inputs
5. **Collects feedback** to improve over time

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                    (React Chat Widget)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP POST /api/chat
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                     (backend/main.py)                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              LANGGRAPH STATE MACHINE                      │ │
│  │                                                           │ │
│  │   ┌─────────┐     ┌─────────┐     ┌──────────────────┐   │ │
│  │   │ ROUTER  │────▶│   RAG   │────▶│  LEAD CAPTURE    │   │ │
│  │   │  AGENT  │     │  AGENT  │     │     AGENT        │   │ │
│  │   └────┬────┘     └────┬────┘     └──────────────────┘   │ │
│  │        │               │                                  │ │
│  │        ▼               ▼                                  │ │
│  │   ┌─────────┐     ┌─────────────────────────────────┐    │ │
│  │   │GUARDRAIL│     │      ENHANCED RAG SYSTEM        │    │ │
│  │   │ CHECKER │     │  ┌─────────┐  ┌─────────────┐   │    │ │
│  │   └─────────┘     │  │ HYBRID  │  │   CLAUDE    │   │    │ │
│  │                   │  │ SEARCH  │  │   SONNET    │   │    │ │
│  │                   │  └────┬────┘  └─────────────┘   │    │ │
│  │                   └───────┼─────────────────────────┘    │ │
│  └───────────────────────────┼───────────────────────────────┘ │
└──────────────────────────────┼──────────────────────────────────┘
                               │ SQL Queries
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL + PGVECTOR                        │
│                      (Docker Container)                         │
│                                                                 │
│   ┌───────────┐  ┌───────────┐  ┌───────────────────────────┐  │
│   │ documents │  │  chunks   │  │     conversations         │  │
│   │  (1,206)  │  │ (15,000+) │  │  + messages + leads       │  │
│   │           │  │           │  │                           │  │
│   │  Scraped  │  │  Chunked  │  │   User session data       │  │
│   │  content  │  │  + vectors│  │   and chat history        │  │
│   └───────────┘  └───────────┘  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Folder Structure Overview

```
stirling_chat/
│
├── backend/                    # FastAPI REST API
│   ├── main.py                 # 7 API endpoints
│   ├── models.py               # Pydantic schemas
│   ├── config.py               # Environment config
│   └── .env                    # API keys (secret)
│
├── frontend/                   # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget.jsx  # Main chat UI
│   │   │   └── FeedbackModal.jsx
│   │   ├── App.jsx
│   │   └── config.js           # API endpoints
│   ├── Dockerfile
│   └── package.json
│
├── scripts/                    # Core AI/ML Logic
│   ├── conversational_system.py  # LangGraph orchestration
│   ├── enhanced_rag.py           # Search + answer generation
│   ├── guardrails.py             # Safety & topic boundaries
│   ├── lead_manager.py           # Lead capture logic
│   ├── feedback_system.py        # Rating collection
│   ├── scrape_to_db.py           # Web scraper
│   ├── process_chunks.py         # Text chunking
│   └── generate_embeddings.py    # Vector embeddings
│
├── database/                   # SQL Schemas
│   ├── schema_conversations.sql
│   └── migration_lead_management_v2.sql
│
├── data/urls/                  # URL lists by category
│
├── docker-compose.yml          # PostgreSQL container
├── requirements.txt            # Python dependencies
└── .env.example                # Environment template
```

---

## 🔄 Data Flow Summary

### 1. User Sends Message
```
User types "What are the fees for MSc AI?"
    ↓
Frontend (ChatWidget.jsx) sends POST to /api/chat
    ↓
Backend (main.py) receives request
```

### 2. Message Processing
```
ConversationalRAGSystem.chat() is called
    ↓
LangGraph routes through agents:
    1. RouterAgent: Classify intent, check guardrails
    2. RAGAgent: Search database, generate answer
    3. LeadCaptureAgent: (if needed) collect contact info
```

### 3. RAG Search
```
User query → OpenAI Embeddings → Vector search in pgvector
    ↓
Top 5 relevant chunks retrieved
    ↓
Chunks + query → Claude Sonnet 4 → Generated answer
```

### 4. Response Returned
```
Answer + sources → Backend formats response
    ↓
JSON response → Frontend displays in chat
```

---

## 🚀 How to Start Reading the Code

### Recommended Order:

1. **Start with the API** (`backend/main.py`)
   - See all 7 endpoints
   - Understand request/response flow

2. **Follow into the RAG System** (`scripts/conversational_system.py`)
   - See the LangGraph state machine
   - Understand the 3-agent architecture

3. **Deep dive into Search** (`scripts/enhanced_rag.py`)
   - Hybrid search algorithm
   - Claude integration

4. **Explore the Frontend** (`frontend/src/components/ChatWidget.jsx`)
   - React state management
   - API integration

5. **Understand the Data** (`database/schema_conversations.sql`)
   - Table structures
   - Relationships

---

## 📖 Continue to Part 1

**Next:** Open `01_PROJECT_OVERVIEW.md` to understand the project objectives and architecture in detail.

---

## Quick Reference: Key Files

| Purpose | File |
|---------|------|
| API Entry Point | `backend/main.py` |
| AI Orchestration | `scripts/conversational_system.py` |
| Search & Answers | `scripts/enhanced_rag.py` |
| Safety Rules | `scripts/guardrails.py` |
| Lead Capture | `scripts/lead_manager.py` |
| Chat UI | `frontend/src/components/ChatWidget.jsx` |
| Database Schema | `database/schema_conversations.sql` |
| Docker Setup | `docker-compose.yml` |
