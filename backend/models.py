"""
============================================
FASTAPI BACKEND - PYDANTIC MODELS
============================================
Purpose: Request and response models for API validation
Version: 1.0
Created: 2025-11-20
============================================
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime


# ============================================
# CHAT MODELS
# ============================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Existing session ID (optional)")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty or just whitespace"""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class Source(BaseModel):
    """Source reference model"""
    title: str
    url: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    session_id: str
    answer: str
    sources: List[Source] = []
    student_type: Optional[str] = None
    student_level: Optional[str] = None
    detected_programs: List[str] = []
    processing_time_ms: int


# ============================================
# CONVERSATION MODELS
# ============================================

class Message(BaseModel):
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ConversationResponse(BaseModel):
    """Response model for conversation history"""
    session_id: str
    conversation_id: int
    messages: List[Message]
    student_type: Optional[str] = None
    student_level: Optional[str] = None
    detected_programs: List[str] = []
    total_messages: int
    created_at: datetime
    lead_captured: bool = False


class EndConversationResponse(BaseModel):
    """Response model for ending conversation"""
    conversation_id: int
    session_id: str
    total_messages: int
    duration_seconds: int
    student_type: Optional[str] = None
    student_level: Optional[str] = None
    programs_discussed: List[str] = []


# ============================================
# FEEDBACK MODELS
# ============================================

class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""
    session_id: str = Field(..., description="Session identifier")
    rating: str = Field(..., description="Feedback rating: bad, average, or good")
    suggestion: Optional[str] = Field(None, max_length=2000, description="Optional suggestion")
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        """Validate rating is one of the allowed values"""
        allowed = ['bad', 'average', 'good']
        if v.lower() not in allowed:
            raise ValueError(f"Rating must be one of: {', '.join(allowed)}")
        return v.lower()


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    feedback_id: int
    success: bool = True
    message: str = "Feedback submitted successfully"


# ============================================
# ADMIN MODELS
# ============================================

class FeedbackStats(BaseModel):
    """Feedback statistics model"""
    total_feedback: int
    good_count: int
    average_count: int
    bad_count: int
    good_percentage: float
    average_percentage: float
    bad_percentage: float
    total_with_suggestions: int
    suggestion_rate: float


class BadFeedbackItem(BaseModel):
    """Single bad feedback item"""
    feedback_id: int
    conversation_id: int
    session_id: str
    suggestion: Optional[str]
    submitted_at: datetime
    student_type: Optional[str]
    total_messages: int
    programs_discussed: Optional[List[str]]
    safety_incidents_count: int


class BadFeedbackResponse(BaseModel):
    """Response model for bad feedback list"""
    count: int
    feedback: List[BadFeedbackItem]


# ============================================
# ERROR MODELS
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================
# HEALTH CHECK MODEL
# ============================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0"
    database_connected: bool
