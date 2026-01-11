# Part 1: Project Overview & Architecture

## 🎯 Learning Objectives

By the end of this section, you will understand:
- The business problem this chatbot solves
- The complete technology stack
- How all components connect together
- The 3-agent architecture design

---

## 1.1 Business Problem

### The Challenge

University admissions teams receive thousands of repetitive questions:
- "What are the fees for MSc Data Science?"
- "What are the entry requirements?"
- "When is the application deadline?"
- "Do you offer scholarships for international students?"

### The Solution

An AI chatbot that:
1. **Answers instantly** using scraped university website content
2. **Provides accurate information** with source links
3. **Captures leads** when queries need human follow-up
4. **Operates 24/7** without human intervention

---

## 1.2 Technology Stack

### Backend (Python)

| Technology | Purpose | File Location |
|------------|---------|---------------|
| **FastAPI** | REST API framework | `backend/main.py` |
| **Pydantic** | Request/response validation | `backend/models.py` |
| **LangGraph** | AI agent orchestration | `scripts/conversational_system.py` |
| **psycopg2** | PostgreSQL database driver | Throughout scripts |

### AI/ML

| Technology | Purpose | File Location |
|------------|---------|---------------|
| **OpenAI API** | Text embeddings (text-embedding-3-small) | `scripts/enhanced_rag.py` |
| **Anthropic API** | LLM responses (Claude Sonnet) | `scripts/enhanced_rag.py` |
| **pgvector** | Vector similarity search | PostgreSQL extension |

### Frontend (JavaScript)

| Technology | Purpose | File Location |
|------------|---------|---------------|
| **React 18** | UI framework | `frontend/src/` |
| **Vite** | Build tool | `frontend/vite.config.js` |
| **TailwindCSS** | Styling | `frontend/tailwind.config.js` |
| **Axios** | HTTP client | `frontend/src/components/` |
| **Lucide React** | Icons | `frontend/src/components/` |

### Infrastructure

| Technology | Purpose | File Location |
|------------|---------|---------------|
| **Docker** | Containerization | `docker-compose.yml`, `frontend/Dockerfile` |
| **PostgreSQL 16** | Database | `docker-compose.yml` |
| **pgvector** | Vector extension | `scripts/init_db.sql` |

---

## 1.3 The 3-Agent Architecture

The chatbot uses **LangGraph** to orchestrate three specialized agents:

```
User Message
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    ROUTER AGENT                         │
│                                                         │
│  Responsibilities:                                      │
│  • Classify user intent (greeting, question, etc.)      │
│  • Run guardrail checks (safety, topic boundaries)      │
│  • Detect student type (UK, international, Scottish)    │
│  • Detect study level (undergraduate, postgraduate)     │
│  • Decide which agent handles the request               │
│                                                         │
│  Key File: scripts/conversational_system.py             │
│  Class: RouterAgent (lines 110-350)                     │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    [greeting]      [question]     [lead_capture]
         │               │               │
         │               ▼               │
         │  ┌────────────────────────┐   │
         │  │       RAG AGENT        │   │
         │  │                        │   │
         │  │  Responsibilities:     │   │
         │  │  • Search database     │   │
         │  │  • Retrieve context    │   │
         │  │  • Generate answer     │   │
         │  │  • Format sources      │   │
         │  │                        │   │
         │  │  Key File:             │   │
         │  │  scripts/enhanced_rag.py│  │
         │  └───────────┬────────────┘   │
         │              │                │
         │              ▼                ▼
         │         [answer]    ┌─────────────────────┐
         │              │      │  LEAD CAPTURE AGENT │
         │              │      │                     │
         │              │      │  Responsibilities:  │
         │              │      │  • Collect name     │
         │              │      │  • Collect email    │
         │              │      │  • Save to database │
         │              │      │  • Notify admissions│
         │              │      │                     │
         │              │      │  Key File:          │
         │              │      │  scripts/           │
         │              │      │  conversational_    │
         │              │      │  system.py          │
         │              │      └──────────┬──────────┘
         │              │                 │
         ▼              ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                    RESPONSE                             │
│                                                         │
│  Formatted answer with sources returned to user         │
└─────────────────────────────────────────────────────────┘
```

---

## 1.4 Key Design Decisions

### Why LangGraph?

LangGraph provides:
- **State management** across conversation turns
- **Conditional routing** between agents
- **Easy debugging** with clear state transitions
- **Extensibility** for adding new agents

### Why Hybrid Search?

The RAG system uses both:
- **Vector search** (semantic similarity via embeddings)
- **Keyword search** (exact term matching)

This ensures:
- "MSc AI fees" finds content about "Artificial Intelligence tuition"
- Exact terms like "£24,300" are matched precisely

### Why Claude Sonnet?

| Model | Cost | Quality | Speed |
|-------|------|---------|-------|
| Claude Haiku | Cheapest | Good | Fastest |
| **Claude Sonnet** | **Balanced** | **Best** | **Fast** |
| Claude Opus | Expensive | Best | Slower |

Sonnet provides the best quality/cost balance for production use.

---

## 1.5 Information Flow - Complete Example

Let's trace a complete request through the system:

### User asks: "What are the fees for MSc AI for international students?"

```
STEP 1: Frontend
─────────────────
ChatWidget.jsx sends POST to /api/chat
{
  "message": "What are the fees for MSc AI for international students?",
  "session_id": "abc-123-xyz"
}

STEP 2: Backend API
─────────────────
main.py receives request
→ Calls rag_system.chat(user_input, session_id)

STEP 3: Router Agent
─────────────────
RouterAgent.__call__(state)
→ Runs guardrails (passes - valid question)
→ Detects intent: "fee_question"
→ Detects student_type: "international"
→ Detects student_level: "postgraduate" (MSc)
→ Sets next_action: "rag"

STEP 4: RAG Agent
─────────────────
RAGAgent.__call__(state)
→ Builds enhanced query: "MSc AI international student fees postgraduate"
→ Calls EnhancedRAG.query()

STEP 5: Hybrid Search
─────────────────
HybridSearch.search(query)
→ Generates embedding via OpenAI
→ Vector search: SELECT * FROM chunks ORDER BY embedding <-> query_embedding
→ Keyword search: SELECT * FROM chunks WHERE content ILIKE '%fee%'
→ Combines and re-ranks results
→ Returns top 5 chunks

STEP 6: Answer Generation
─────────────────
AnswerGenerator.generate(query, chunks)
→ Builds system prompt (personality, rules)
→ Builds user prompt (context + question)
→ Calls Claude Sonnet API
→ Returns formatted answer

STEP 7: Response
─────────────────
{
  "session_id": "abc-123-xyz",
  "answer": "MSc AI fees for international students are £24,300/year...",
  "sources": ["https://www.stir.ac.uk/courses/msc-ai/"],
  "student_type": "international",
  "student_level": "postgraduate",
  "processing_time_ms": 1250
}

STEP 8: Frontend Display
─────────────────
ChatWidget.jsx renders message with sources
User sees formatted response with clickable links
```

---

## 1.6 Code Reading Exercise

### Exercise 1: Trace the Entry Point

Open `backend/main.py` and find:
1. The `/api/chat` endpoint (around line 178)
2. Where `rag_system.chat()` is called
3. How the response is formatted

### Exercise 2: Find the State Machine

Open `scripts/conversational_system.py` and find:
1. The `ConversationState` TypedDict (around line 42)
2. The `create_conversational_graph()` function (around line 962)
3. The routing logic `route_after_router()` (around line 999)

### Exercise 3: Understand the Agents

In `scripts/conversational_system.py`, locate:
1. `RouterAgent` class - What does `__call__` do?
2. `RAGAgent` class - How does it call the search?
3. `LeadCaptureAgent` class - When is it triggered?

---

## 📖 Continue to Part 2

**Next:** Open `02_DATABASE_AND_DOCKER.md` to understand the database schema and Docker setup.

---

## Quick Reference

| Concept | Location |
|---------|----------|
| API Entry | `backend/main.py:178` |
| State Definition | `scripts/conversational_system.py:42` |
| Router Agent | `scripts/conversational_system.py:110` |
| RAG Agent | `scripts/conversational_system.py:354` |
| Lead Capture Agent | `scripts/conversational_system.py:527` |
| Graph Creation | `scripts/conversational_system.py:962` |
