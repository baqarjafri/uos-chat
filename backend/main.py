"""
============================================
FASTAPI BACKEND - MAIN APPLICATION
============================================
Purpose: RESTful API for Stirling University Chatbot
Endpoints: 7 essential endpoints for chat and feedback
Version: 1.0
Created: 2025-11-20
============================================
"""

import sys
import os
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from models import (
    ChatRequest, ChatResponse, Source,
    ConversationResponse, Message, EndConversationResponse,
    FeedbackRequest, FeedbackResponse,
    FeedbackStats, BadFeedbackResponse, BadFeedbackItem,
    ErrorResponse, HealthResponse
)

# Import our conversational system
from scripts.conversational_system import ConversationalRAGSystem
from scripts.feedback_system import FeedbackManager


# ============================================
# FASTAPI APP INITIALIZATION
# ============================================

app = FastAPI(
    title="Stirling University Chatbot API",
    description="Conversational RAG system with feedback collection",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# GLOBAL STATE
# ============================================

# Initialize conversational system (singleton)
rag_system: Optional[ConversationalRAGSystem] = None
feedback_manager: Optional[FeedbackManager] = None
db_connection = None


# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global rag_system, feedback_manager, db_connection
    
    try:
        # Initialize database connection
        db_connection = psycopg2.connect(settings.DATABASE_URL)
        
        # Initialize RAG system
        rag_system = ConversationalRAGSystem(
            db_connection_string=settings.DATABASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            anthropic_api_key=settings.ANTHROPIC_API_KEY
        )
        
        # Initialize feedback manager
        feedback_manager = FeedbackManager(db_connection)
        
        print("[OK] FastAPI backend started successfully!")
        print(f"[DB] Database: Connected")
        print(f"[RAG] RAG System: Initialized")
        print(f"[FEEDBACK] Feedback System: Ready")
        
    except Exception as e:
        print(f"[ERROR] Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global rag_system, db_connection
    
    if rag_system:
        rag_system.close()
    
    if db_connection:
        db_connection.close()
    
    print("[SHUTDOWN] FastAPI backend shut down")


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
            "status_code": 500
        }
    )


# ============================================
# ENDPOINTS
# ============================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns system status and database connectivity
    """
    db_connected = False
    
    try:
        if db_connection:
            cursor = db_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            db_connected = True
    except:
        pass
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(),
        version="1.0",
        database_connected=db_connected
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """
    Main chat endpoint
    
    Process user message and return AI response with sources.
    Creates new session if session_id not provided.
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Reset any bad transactions
        if db_connection:
            try:
                db_connection.rollback()
            except:
                pass
        
        # Get user IP address
        ip_address = http_request.client.host if http_request.client else None
        
        # Process chat
        response = rag_system.chat(
            user_input=request.message,
            session_id=request.session_id,
            ip_address=ip_address
        )
        
        # Format sources with rich metadata
        sources = []
        for src in response.get("sources", []):
            if isinstance(src, str):
                # Source is a URL string (legacy format)
                sources.append(Source(
                    title="Source",
                    url=src,
                    category=None,
                    relevance_score=None
                ))
            elif isinstance(src, dict):
                # Source is a dict with rich metadata
                sources.append(Source(
                    title=src.get("title", "Source"),
                    url=src.get("url", ""),
                    category=src.get("category"),
                    relevance_score=src.get("relevance_score")
                ))
            else:
                # Skip invalid sources
                continue
        
        return ChatResponse(
            session_id=response["session_id"],
            answer=response["answer"],
            sources=sources,
            student_type=response.get("student_type"),
            student_level=response.get("student_level"),
            detected_programs=response.get("detected_programs", []),
            processing_time_ms=response.get("processing_time_ms", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.get("/api/conversation/{session_id}", response_model=ConversationResponse)
async def get_conversation(session_id: str):
    """
    Get conversation history
    
    Retrieve full conversation history for a session.
    Useful for showing history on page refresh.
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Get session from system
        if session_id not in rag_system.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = rag_system.sessions[session_id]
        
        # Format messages
        messages = []
        for i in range(0, len(session["messages"]), 2):
            if i < len(session["messages"]):
                # User message
                messages.append(Message(
                    role="user",
                    content=session["messages"][i].content,
                    timestamp=datetime.now()  # Approximate
                ))
            if i + 1 < len(session["messages"]):
                # Assistant message
                messages.append(Message(
                    role="assistant",
                    content=session["messages"][i + 1].content,
                    timestamp=datetime.now()  # Approximate
                ))
        
        # Get conversation details from database
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, created_at, lead_captured
            FROM conversations
            WHERE session_id = %s
        """, (session_id,))
        
        conv = cursor.fetchone()
        
        return ConversationResponse(
            session_id=session_id,
            conversation_id=conv['id'] if conv else session["conversation_id"],
            messages=messages,
            student_type=session.get("student_type"),
            student_level=session.get("student_level"),
            detected_programs=session.get("detected_programs", []),
            total_messages=len(messages),
            created_at=conv['created_at'] if conv else datetime.now(),
            lead_captured=conv['lead_captured'] if conv else False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


@app.post("/api/conversation/{session_id}/end", response_model=EndConversationResponse)
async def end_conversation(session_id: str):
    """
    End conversation
    
    Mark conversation as ended and return summary.
    This triggers the feedback modal on frontend.
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        summary = rag_system.end_conversation(session_id)
        
        return EndConversationResponse(
            conversation_id=summary["conversation_id"],
            session_id=summary["session_id"],
            total_messages=summary["total_messages"],
            duration_seconds=summary["duration_seconds"],
            student_type=summary.get("student_type"),
            student_level=summary.get("student_level"),
            programs_discussed=summary.get("programs_discussed", [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")


@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, http_request: Request):
    """
    Submit feedback
    
    Submit user feedback for a conversation.
    Rating: bad, average, or good
    Suggestion: optional text feedback
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Get user info
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        # Submit feedback
        feedback_id = rag_system.submit_feedback(
            session_id=request.session_id,
            rating=request.rating,
            suggestion=request.suggestion,
            user_ip_address=ip_address,
            user_agent=user_agent
        )
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            success=True,
            message="Thank you for your feedback!"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@app.get("/api/admin/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats(days: int = 30):
    """
    Get feedback statistics (Admin)
    
    Returns aggregated feedback statistics for the specified time period.
    Default: last 30 days
    """
    if not feedback_manager:
        raise HTTPException(status_code=503, detail="Feedback system not initialized")
    
    try:
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        stats = feedback_manager.get_feedback_stats(start_date, end_date)
        
        return FeedbackStats(
            total_feedback=stats.total_feedback,
            good_count=stats.good_count,
            average_count=stats.average_count,
            bad_count=stats.bad_count,
            good_percentage=stats.good_percentage,
            average_percentage=stats.average_percentage,
            bad_percentage=stats.bad_percentage,
            total_with_suggestions=stats.total_with_suggestions,
            suggestion_rate=stats.suggestion_rate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


@app.get("/api/admin/feedback/bad", response_model=BadFeedbackResponse)
async def get_bad_feedback(limit: int = 10):
    """
    Get unreviewed bad feedback (Admin)
    
    Returns list of unreviewed bad feedback for priority review.
    Default limit: 10
    """
    if not feedback_manager:
        raise HTTPException(status_code=503, detail="Feedback system not initialized")
    
    try:
        bad_feedback = feedback_manager.get_unreviewed_bad_feedback(limit=limit)
        
        feedback_items = [
            BadFeedbackItem(
                feedback_id=fb['feedback_id'],
                conversation_id=fb['conversation_id'],
                session_id=fb['session_id'],
                suggestion=fb.get('suggestion'),
                submitted_at=fb['submitted_at'],
                student_type=fb.get('student_type'),
                total_messages=fb['total_messages'],
                programs_discussed=fb.get('programs_discussed'),
                safety_incidents_count=fb.get('safety_incidents_count', 0)
            )
            for fb in bad_feedback
        ]
        
        return BadFeedbackResponse(
            count=len(feedback_items),
            feedback=feedback_items
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bad feedback: {str(e)}")


# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Stirling University Chatbot API",
        "version": "1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "chat": "POST /api/chat",
            "conversation": "GET /api/conversation/{session_id}",
            "end_conversation": "POST /api/conversation/{session_id}/end",
            "feedback": "POST /api/feedback",
            "admin_stats": "GET /api/admin/feedback/stats",
            "admin_bad_feedback": "GET /api/admin/feedback/bad"
        }
    }


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
