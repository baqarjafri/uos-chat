# Part 3: Backend & API Deep Dive

## 🎯 Learning Objectives

By the end of this section, you will understand:
- FastAPI application structure
- All 7 API endpoints and their purposes
- Request/response models with Pydantic
- How the backend connects to the RAG system
- Error handling and CORS configuration

---

## 3.1 FastAPI Overview

### Why FastAPI?

| Feature | Benefit |
|---------|---------|
| **Async support** | Handle many concurrent requests |
| **Auto documentation** | Swagger UI at `/docs` |
| **Type validation** | Pydantic models catch errors |
| **Fast** | One of the fastest Python frameworks |

### Application Entry Point

**File:** `backend/main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Stirling University Chatbot API",
    description="Conversational RAG system with feedback collection",
    version="1.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc"     # Alternative docs
)
```

---

## 3.2 Configuration

**File:** `backend/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Required
    DATABASE_URL: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    
    # Optional with defaults
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Environment Variables

**File:** `backend/.env`

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/stirling_chat
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=http://localhost:3000
```

---

## 3.3 CORS Configuration

CORS (Cross-Origin Resource Sharing) allows the frontend to call the backend.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],      # GET, POST, etc.
    allow_headers=["*"],      # All headers allowed
)
```

### Why CORS Matters

```
Frontend (localhost:3000) ──POST──▶ Backend (localhost:8001)
                                          │
                                          ▼
                                    CORS Check:
                                    Is localhost:3000 allowed?
                                          │
                                    ┌─────┴─────┐
                                    │           │
                                   YES          NO
                                    │           │
                                    ▼           ▼
                              Process      403 Forbidden
                              Request
```

---

## 3.4 Startup & Shutdown Events

**Lines 76-113 in `main.py`:**

```python
# Global state
rag_system: Optional[ConversationalRAGSystem] = None
feedback_manager: Optional[FeedbackManager] = None
db_connection = None

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global rag_system, feedback_manager, db_connection
    
    # 1. Connect to database
    db_connection = psycopg2.connect(settings.DATABASE_URL)
    
    # 2. Initialize RAG system
    rag_system = ConversationalRAGSystem(
        db_connection_string=settings.DATABASE_URL,
        openai_api_key=settings.OPENAI_API_KEY,
        anthropic_api_key=settings.ANTHROPIC_API_KEY
    )
    
    # 3. Initialize feedback manager
    feedback_manager = FeedbackManager(db_connection)
    
    print("[OK] FastAPI backend started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_connection
    if db_connection:
        db_connection.close()
```

---

## 3.5 Pydantic Models

**File:** `backend/models.py`

Pydantic models define the shape of requests and responses.

### Chat Request

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()
```

### Chat Response

```python
class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[Source] = []
    student_type: Optional[str] = None
    student_level: Optional[str] = None
    detected_programs: List[str] = []
    processing_time_ms: int
```

### Source Model

```python
class Source(BaseModel):
    title: str
    url: str
    relevance_score: Optional[float] = None
```

---

## 3.6 API Endpoints

### Endpoint 1: Health Check

**GET /health**

```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if system is healthy"""
    db_connected = False
    
    try:
        cursor = db_connection.cursor()
        cursor.execute("SELECT 1")
        db_connected = True
    except:
        pass
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(),
        database_connected=db_connected
    )
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T17:00:00",
  "version": "1.0",
  "database_connected": true
}
```

---

### Endpoint 2: Chat (Main Endpoint)

**POST /api/chat**

This is the core endpoint that processes user messages.

```python
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """Process user message and return AI response"""
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Get user IP for rate limiting
    ip_address = http_request.client.host
    
    # Process through RAG system
    response = rag_system.chat(
        user_input=request.message,
        session_id=request.session_id,
        ip_address=ip_address
    )
    
    # Format sources
    sources = []
    for src in response.get("sources", []):
        sources.append(Source(
            title="Source",
            url=src if isinstance(src, str) else src.get("url", "")
        ))
    
    return ChatResponse(
        session_id=response["session_id"],
        answer=response["answer"],
        sources=sources,
        student_type=response.get("student_type"),
        student_level=response.get("student_level"),
        detected_programs=response.get("detected_programs", []),
        processing_time_ms=response.get("processing_time_ms", 0)
    )
```

**Request:**
```json
{
  "message": "What are the fees for MSc AI?",
  "session_id": "abc-123-xyz"
}
```

**Response:**
```json
{
  "session_id": "abc-123-xyz",
  "answer": "MSc AI fees are £24,300/year for international students...",
  "sources": [
    {"title": "Source", "url": "https://stir.ac.uk/courses/msc-ai/"}
  ],
  "student_type": "international",
  "student_level": "postgraduate",
  "detected_programs": ["artificial intelligence"],
  "processing_time_ms": 1250
}
```

---

### Endpoint 3: Get Conversation History

**GET /api/conversation/{session_id}**

```python
@app.get("/api/conversation/{session_id}", response_model=ConversationResponse)
async def get_conversation(session_id: str):
    """Retrieve full conversation history for a session"""
    
    if session_id not in rag_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = rag_system.sessions[session_id]
    
    # Format messages
    messages = []
    for msg in session["messages"]:
        messages.append(Message(
            role=msg.role,
            content=msg.content,
            timestamp=datetime.now()
        ))
    
    return ConversationResponse(
        session_id=session_id,
        messages=messages,
        student_type=session.get("student_type"),
        # ... other fields
    )
```

---

### Endpoint 4: End Conversation

**POST /api/conversation/{session_id}/end**

```python
@app.post("/api/conversation/{session_id}/end", response_model=EndConversationResponse)
async def end_conversation(session_id: str):
    """End a conversation and get summary"""
    
    if session_id not in rag_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = rag_system.sessions[session_id]
    
    # Calculate duration
    duration = int((datetime.now() - session["created_at"]).total_seconds())
    
    return EndConversationResponse(
        conversation_id=session["conversation_id"],
        session_id=session_id,
        total_messages=len(session["messages"]),
        duration_seconds=duration,
        programs_discussed=session.get("detected_programs", [])
    )
```

---

### Endpoint 5: Submit Feedback

**POST /api/feedback**

```python
@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for a conversation"""
    
    # Get conversation ID from session
    if request.session_id not in rag_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = rag_system.sessions[request.session_id]
    conversation_id = session.get("conversation_id")
    
    # Save feedback
    feedback_id = feedback_manager.submit_feedback(
        conversation_id=conversation_id,
        session_id=request.session_id,
        rating=request.rating,
        suggestion=request.suggestion
    )
    
    return FeedbackResponse(
        feedback_id=feedback_id,
        success=True,
        message="Feedback submitted successfully"
    )
```

**Request:**
```json
{
  "session_id": "abc-123-xyz",
  "rating": "good",
  "suggestion": "Very helpful!"
}
```

---

### Endpoint 6: Get Feedback Stats

**GET /api/feedback/stats**

```python
@app.get("/api/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """Get aggregated feedback statistics"""
    
    stats = feedback_manager.get_stats()
    
    return FeedbackStats(
        total_feedback=stats["total"],
        good_count=stats["good"],
        average_count=stats["average"],
        bad_count=stats["bad"],
        good_percentage=stats["good_pct"],
        # ... other fields
    )
```

---

### Endpoint 7: Get Bad Feedback

**GET /api/feedback/bad**

```python
@app.get("/api/feedback/bad", response_model=BadFeedbackResponse)
async def get_bad_feedback(limit: int = 50):
    """Get list of bad feedback for review"""
    
    feedback_list = feedback_manager.get_bad_feedback(limit=limit)
    
    return BadFeedbackResponse(
        count=len(feedback_list),
        feedback=feedback_list
    )
```

---

## 3.7 Error Handling

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )
```

---

## 3.8 Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        POST /api/chat                           │
│                                                                 │
│  Request Body:                                                  │
│  {"message": "What are MSc AI fees?", "session_id": null}      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Pydantic Validation (ChatRequest)                          │
│     • message: min 1 char, max 2000                            │
│     • session_id: optional                                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Check RAG System Initialized                                │
│     if not rag_system: raise HTTPException(503)                │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Call rag_system.chat()                                      │
│     • Creates/retrieves session                                 │
│     • Runs through LangGraph agents                            │
│     • Returns answer + metadata                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Format Response (ChatResponse)                              │
│     • session_id: "new-uuid-here"                              │
│     • answer: "MSc AI fees are..."                             │
│     • sources: [{"url": "..."}]                                │
│     • processing_time_ms: 1250                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Return JSON Response                                        │
│     HTTP 200 OK                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3.9 Code Reading Exercise

### Exercise 1: Trace the Chat Endpoint

Open `backend/main.py` and:
1. Find the `/api/chat` endpoint (line ~178)
2. Identify where `rag_system.chat()` is called
3. See how sources are formatted
4. Find where `processing_time_ms` comes from

### Exercise 2: Understand Validation

Open `backend/models.py` and:
1. Find the `ChatRequest` model
2. Look at the `@field_validator` decorator
3. Understand what happens if message is empty

### Exercise 3: Test the API

```bash
# Health check
curl http://localhost:8001/health

# Send a chat message
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Open Swagger UI
# Navigate to: http://localhost:8001/docs
```

---

## 📖 Continue to Part 4

**Next:** Open `04_RAG_SYSTEM.md` to understand the AI brain - search, embeddings, and Claude integration.

---

## Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health check |
| `/api/chat` | POST | Main chat endpoint |
| `/api/conversation/{id}` | GET | Get chat history |
| `/api/conversation/{id}/end` | POST | End conversation |
| `/api/feedback` | POST | Submit rating |
| `/api/feedback/stats` | GET | Feedback statistics |
| `/api/feedback/bad` | GET | Bad feedback list |
