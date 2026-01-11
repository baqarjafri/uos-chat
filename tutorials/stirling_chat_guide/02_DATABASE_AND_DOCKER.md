# Part 2: Database & Docker Infrastructure

## 🎯 Learning Objectives

By the end of this section, you will understand:
- The Docker setup and why we use containers
- PostgreSQL with pgvector extension
- Complete database schema design
- How data flows between tables
- Vector embeddings storage and search

---

## 2.1 Docker Setup

### Why Docker?

Docker provides:
- **Consistency**: Same environment on every machine
- **Isolation**: Database doesn't conflict with local installations
- **Easy setup**: One command to start everything
- **Portability**: Works on Windows, Mac, Linux

### The docker-compose.yml File

**Location:** `stirling_chat/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16      # PostgreSQL 16 with vector extension
    container_name: stirling_chat_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: stirling_chat
    ports:
      - "5433:5432"                     # Host:Container (5433 to avoid conflicts)
    volumes:
      - postgres_data:/var/lib/postgresql/data    # Persist data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql  # Init script
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local
```

### Key Points:

| Setting | Value | Why |
|---------|-------|-----|
| **Port** | 5433:5432 | Avoids conflict with local PostgreSQL on 5432 |
| **Image** | pgvector/pgvector:pg16 | Includes vector extension pre-installed |
| **Volume** | postgres_data | Data persists even if container restarts |
| **Init Script** | init_db.sql | Creates pgvector extension on first run |

### Docker Commands

```bash
# Start the database
docker-compose up -d

# Check if running
docker ps

# View logs
docker logs stirling_chat_db

# Stop the database
docker-compose down

# Stop and delete all data (careful!)
docker-compose down -v
```

---

## 2.2 The pgvector Extension

### What is pgvector?

pgvector adds **vector similarity search** to PostgreSQL. This enables:
- Storing embeddings (1536-dimensional vectors)
- Finding similar content using cosine distance
- Semantic search (meaning-based, not just keyword)

### How It Works

```
User Query: "What are the fees?"
                │
                ▼
┌─────────────────────────────────┐
│  OpenAI Embedding API           │
│  text-embedding-3-small         │
│                                 │
│  Output: [0.023, -0.041, ...]   │
│          (1536 dimensions)      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  PostgreSQL + pgvector          │
│                                 │
│  SELECT * FROM chunks           │
│  ORDER BY embedding <-> $1      │  ← Cosine distance operator
│  LIMIT 5;                       │
│                                 │
│  Returns: Top 5 most similar    │
│           chunks by meaning     │
└─────────────────────────────────┘
```

### The `<->` Operator

pgvector provides distance operators:
- `<->` : L2 (Euclidean) distance
- `<=>` : Cosine distance
- `<#>` : Inner product

We use `<->` for similarity search.

---

## 2.3 Database Schema Overview

The database has **8 main tables**:

```
┌─────────────────┐     ┌─────────────────┐
│   documents     │────▶│     chunks      │
│   (1,206 rows)  │     │   (15,000+)     │
│                 │     │                 │
│  Scraped pages  │     │  Text segments  │
│  from website   │     │  + embeddings   │
└─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ conversations   │────▶│    messages     │     │     leads       │
│                 │     │                 │     │                 │
│  User sessions  │     │  Chat history   │     │  Contact info   │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         ├──────────────▶┌─────────────────┐
         │               │conversation_    │
         │               │feedback         │
         │               └─────────────────┘
         │
         └──────────────▶┌─────────────────┐
                         │safety_incidents │
                         └─────────────────┘
```

---

## 2.4 Table: documents

**Purpose:** Stores scraped web pages from the university website.

**Location:** Created by `scripts/scrape_to_db.py`

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,           -- Page URL
    title TEXT,                         -- Page title
    content TEXT,                       -- Full markdown content
    category TEXT,                      -- courses, fees, admissions, etc.
    scraped_at TIMESTAMP DEFAULT NOW(),
    content_length INTEGER,             -- Character count
    chunk_count INTEGER DEFAULT 0,      -- Number of chunks created
    js_rendered BOOLEAN DEFAULT FALSE,  -- Was JavaScript executed?
    metadata JSONB DEFAULT '{}'         -- Additional data
);
```

### Sample Data:

| id | url | title | category | content_length |
|----|-----|-------|----------|----------------|
| 1 | https://stir.ac.uk/courses/msc-ai | MSc Artificial Intelligence | courses | 15,234 |
| 2 | https://stir.ac.uk/fees | Tuition Fees | fees | 8,456 |

---

## 2.5 Table: chunks

**Purpose:** Stores text segments with vector embeddings for search.

**Location:** Created by `scripts/process_chunks.py` and `scripts/generate_embeddings.py`

```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,              -- The text chunk (800 tokens max)
    heading_context TEXT,               -- e.g., "MSc AI > Entry Requirements"
    chunk_index INTEGER,                -- Position in document
    token_count INTEGER,                -- Number of tokens
    embedding VECTOR(1536),             -- OpenAI embedding vector
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast vector search
CREATE INDEX ON chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
```

### How Chunks Are Created:

```
Original Document (15,000 characters)
              │
              ▼
┌─────────────────────────────────────┐
│  LangChain RecursiveCharacterSplitter│
│                                     │
│  Settings:                          │
│  • chunk_size: 800 tokens           │
│  • chunk_overlap: 200 tokens        │
│  • Respects markdown headings       │
└─────────────────────────────────────┘
              │
              ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Chunk 1 │ │ Chunk 2 │ │ Chunk 3 │  ... (20 chunks)
│ 800 tok │ │ 800 tok │ │ 800 tok │
└─────────┘ └─────────┘ └─────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  OpenAI Embeddings API              │
│  text-embedding-3-small             │
│                                     │
│  Each chunk → 1536-dim vector       │
└─────────────────────────────────────┘
              │
              ▼
        Stored in chunks.embedding
```

---

## 2.6 Table: conversations

**Purpose:** Tracks user chat sessions and detected information.

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,  -- Browser session ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    
    -- Detected user information
    student_type VARCHAR(50),           -- scottish, uk, eu, international
    student_level VARCHAR(50),          -- undergraduate, postgraduate, phd
    detected_location VARCHAR(255),
    user_name VARCHAR(100),
    
    -- Conversation stats
    total_messages INTEGER DEFAULT 0,
    programs_discussed TEXT[],          -- Array of program names
    topics_covered TEXT[],
    
    -- Lead capture
    lead_captured BOOLEAN DEFAULT FALSE,
    lead_id INTEGER,
    lead_data JSONB DEFAULT '{}',
    
    -- Quality tracking
    flagged_for_review BOOLEAN DEFAULT FALSE,
    safety_incidents_count INTEGER DEFAULT 0
);
```

### Session Flow:

```
User opens chat
      │
      ▼
Frontend generates session_id (UUID)
      │
      ▼
First message creates conversation row
      │
      ▼
Each message updates:
  • total_messages
  • student_type (if detected)
  • student_level (if detected)
  • programs_discussed (if mentioned)
      │
      ▼
User closes chat → ended_at set
```

---

## 2.7 Table: messages

**Purpose:** Stores individual chat messages for history.

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,          -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Metadata
    intent VARCHAR(50),                 -- greeting, fee_question, etc.
    confidence FLOAT,
    sources TEXT[],                     -- URLs used for response
    response_time_ms INTEGER
);
```

### Example Messages:

| id | conversation_id | role | content | intent |
|----|-----------------|------|---------|--------|
| 1 | 42 | user | "Hi" | greeting |
| 2 | 42 | assistant | "Hey! 👋 Welcome to Stirling..." | greeting |
| 3 | 42 | user | "What are MSc AI fees?" | fee_question |
| 4 | 42 | assistant | "MSc AI fees are £24,300..." | fee_question |

---

## 2.8 Table: leads

**Purpose:** Stores contact information for admissions follow-up.

```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Contact info
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(255),
    
    -- Interest info
    student_type VARCHAR(50),
    student_level VARCHAR(50),
    programs_interested TEXT[],
    
    -- Context for admissions team
    user_query TEXT,                    -- What they asked
    conversation_summary TEXT,          -- AI-generated summary
    escalation_reason TEXT,             -- Why escalated
    last_messages JSONB,                -- Recent chat history
    
    -- Status
    status VARCHAR(50) DEFAULT 'new',   -- new, contacted, converted
    contacted_at TIMESTAMP,
    notes TEXT
);
```

---

## 2.9 Table: conversation_feedback

**Purpose:** Stores user ratings and suggestions.

```sql
CREATE TABLE conversation_feedback (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    
    -- Rating
    rating VARCHAR(20) NOT NULL,        -- 'bad', 'average', 'good'
    suggestion TEXT,
    has_suggestion BOOLEAN DEFAULT FALSE,
    
    -- Context
    total_messages_in_conversation INTEGER,
    conversation_duration_seconds INTEGER,
    
    -- Review status
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(255),
    action_taken TEXT,
    
    submitted_at TIMESTAMP DEFAULT NOW()
);
```

---

## 2.10 Table: safety_incidents

**Purpose:** Logs guardrail violations for review.

```sql
CREATE TABLE safety_incidents (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    session_id VARCHAR(255),
    
    -- Incident details
    incident_type VARCHAR(50),          -- harassment, off_topic, prompt_injection
    severity VARCHAR(20),               -- low, medium, high, critical
    user_input TEXT,                    -- What triggered it
    detected_patterns TEXT[],           -- Matched patterns
    
    -- Response
    response_given TEXT,                -- What we replied
    
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT FALSE
);
```

---

## 2.11 Database Connection in Code

### Connection String Format

```
postgresql://username:password@host:port/database
postgresql://postgres:postgres@localhost:5433/stirling_chat
```

### Python Connection Example

**From `scripts/conversational_system.py`:**

```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect
conn = psycopg2.connect(
    "postgresql://postgres:postgres@localhost:5433/stirling_chat"
)

# Query with dict results
cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT * FROM chunks WHERE id = %s", (chunk_id,))
row = cursor.fetchone()  # Returns {'id': 1, 'content': '...', ...}

# Always commit after INSERT/UPDATE
conn.commit()
```

---

## 2.12 Code Reading Exercise

### Exercise 1: Explore the Schema

Connect to the database and explore:

```bash
# Connect to database
docker exec -it stirling_chat_db psql -U postgres -d stirling_chat

# List all tables
\dt

# Describe a table
\d chunks

# Count rows
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM chunks;

# Exit
\q
```

### Exercise 2: Find Vector Search

Open `scripts/enhanced_rag.py` and find:
1. The `HybridSearch` class
2. The SQL query that uses `<->` operator
3. How results are combined and ranked

### Exercise 3: Trace Message Storage

Open `scripts/conversational_system.py` and find:
1. `ConversationManager.save_message()` method
2. How messages are inserted into the database
3. How conversation state is updated

---

## 📖 Continue to Part 3

**Next:** Open `03_BACKEND_API.md` to understand the FastAPI endpoints and request handling.

---

## Quick Reference

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| documents | Scraped pages | url, content, category |
| chunks | Text + vectors | content, embedding, heading_context |
| conversations | User sessions | session_id, student_type, lead_captured |
| messages | Chat history | role, content, intent |
| leads | Contact info | name, email, programs_interested |
| conversation_feedback | Ratings | rating, suggestion |
| safety_incidents | Violations | incident_type, severity |
