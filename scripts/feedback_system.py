"""
============================================
CONVERSATION FEEDBACK SYSTEM
============================================
Purpose: Collect and manage user feedback for conversation quality improvement
Features:
- 3-level rating system (bad, average, good)
- Optional textual suggestions
- Automatic conversation flagging for bad ratings
- Analytics and reporting

Version: 1.0
Created: 2025-11-20
============================================
"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor


# ============================================
# DATA MODELS
# ============================================

@dataclass
class FeedbackSubmission:
    """Feedback submission data"""
    conversation_id: int
    session_id: str
    rating: str  # 'bad', 'average', 'good'
    suggestion: Optional[str] = None
    total_messages: Optional[int] = None
    conversation_duration_seconds: Optional[int] = None
    feedback_categories: Optional[List[str]] = None
    user_ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class FeedbackRecord:
    """Complete feedback record"""
    id: int
    conversation_id: int
    session_id: str
    rating: str
    suggestion: Optional[str]
    has_suggestion: bool
    total_messages_in_conversation: int
    conversation_duration_seconds: int
    feedback_categories: List[str]
    submitted_at: datetime
    reviewed: bool
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    action_taken: Optional[str]


@dataclass
class FeedbackStats:
    """Feedback statistics"""
    total_feedback: int
    good_count: int
    average_count: int
    bad_count: int
    good_percentage: float
    average_percentage: float
    bad_percentage: float
    total_with_suggestions: int
    suggestion_rate: float


# ============================================
# FEEDBACK MANAGER
# ============================================

class FeedbackManager:
    """
    Manages conversation feedback collection and analysis
    """
    
    VALID_RATINGS = ['bad', 'average', 'good']
    
    def __init__(self, db_connection):
        """
        Initialize feedback manager
        
        Args:
            db_connection: PostgreSQL connection
        """
        self.conn = db_connection
    
    def submit_feedback(
        self,
        conversation_id: int,
        session_id: str,
        rating: str,
        suggestion: Optional[str] = None,
        total_messages: Optional[int] = None,
        conversation_duration_seconds: Optional[int] = None,
        feedback_categories: Optional[List[str]] = None,
        user_ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Submit feedback for a conversation
        
        Args:
            conversation_id: ID of the conversation
            session_id: Session identifier
            rating: Feedback rating ('bad', 'average', 'good')
            suggestion: Optional textual suggestion
            total_messages: Number of messages in conversation
            conversation_duration_seconds: Duration of conversation
            feedback_categories: Categories for the feedback
            user_ip_address: User's IP address
            user_agent: User's browser/device info
            
        Returns:
            Feedback ID
            
        Raises:
            ValueError: If rating is invalid
        """
        # Validate rating
        if rating not in self.VALID_RATINGS:
            raise ValueError(f"Invalid rating. Must be one of: {', '.join(self.VALID_RATINGS)}")
        
        cursor = self.conn.cursor()
        
        # Check if feedback already exists for this conversation
        cursor.execute(
            "SELECT id FROM conversation_feedback WHERE conversation_id = %s",
            (conversation_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            raise ValueError(f"Feedback already submitted for conversation {conversation_id}")
        
        # Insert feedback
        cursor.execute("""
            INSERT INTO conversation_feedback (
                conversation_id,
                session_id,
                rating,
                suggestion,
                has_suggestion,
                total_messages_in_conversation,
                conversation_duration_seconds,
                feedback_categories,
                user_ip_address,
                user_agent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            conversation_id,
            session_id,
            rating,
            suggestion,
            suggestion is not None and len(suggestion.strip()) > 0,
            total_messages,
            conversation_duration_seconds,
            feedback_categories or [],
            user_ip_address,
            user_agent
        ))
        
        feedback_id = cursor.fetchone()[0]
        self.conn.commit()
        
        return feedback_id
    
    def get_feedback(self, feedback_id: int) -> Optional[FeedbackRecord]:
        """
        Get feedback by ID
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            FeedbackRecord or None if not found
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM conversation_feedback
            WHERE id = %s
        """, (feedback_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return FeedbackRecord(
            id=row['id'],
            conversation_id=row['conversation_id'],
            session_id=row['session_id'],
            rating=row['rating'],
            suggestion=row['suggestion'],
            has_suggestion=row['has_suggestion'],
            total_messages_in_conversation=row['total_messages_in_conversation'],
            conversation_duration_seconds=row['conversation_duration_seconds'],
            feedback_categories=row['feedback_categories'] or [],
            submitted_at=row['submitted_at'],
            reviewed=row['reviewed'],
            reviewed_at=row['reviewed_at'],
            reviewed_by=row['reviewed_by'],
            action_taken=row['action_taken']
        )
    
    def get_feedback_by_conversation(self, conversation_id: int) -> Optional[FeedbackRecord]:
        """
        Get feedback for a specific conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            FeedbackRecord or None if not found
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM conversation_feedback
            WHERE conversation_id = %s
        """, (conversation_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return FeedbackRecord(
            id=row['id'],
            conversation_id=row['conversation_id'],
            session_id=row['session_id'],
            rating=row['rating'],
            suggestion=row['suggestion'],
            has_suggestion=row['has_suggestion'],
            total_messages_in_conversation=row['total_messages_in_conversation'],
            conversation_duration_seconds=row['conversation_duration_seconds'],
            feedback_categories=row['feedback_categories'] or [],
            submitted_at=row['submitted_at'],
            reviewed=row['reviewed'],
            reviewed_at=row['reviewed_at'],
            reviewed_by=row['reviewed_by'],
            action_taken=row['action_taken']
        )
    
    def mark_as_reviewed(
        self,
        feedback_id: int,
        reviewer_name: str,
        action_taken: str
    ) -> bool:
        """
        Mark feedback as reviewed
        
        Args:
            feedback_id: Feedback ID
            reviewer_name: Name of reviewer
            action_taken: Description of action taken
            
        Returns:
            True if successful, False if feedback not found
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT mark_feedback_reviewed(%s, %s, %s)
        """, (feedback_id, reviewer_name, action_taken))
        
        self.conn.commit()
        return True
    
    def get_unreviewed_bad_feedback(self, limit: int = 50) -> List[Dict]:
        """
        Get unreviewed bad feedback (priority for review)
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of feedback records with context
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM unreviewed_bad_feedback
            LIMIT %s
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_feedback_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> FeedbackStats:
        """
        Get feedback statistics for a date range
        
        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)
            
        Returns:
            FeedbackStats object
        """
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM get_feedback_stats(%s, %s)
        """, (start_date, end_date))
        
        row = cursor.fetchone()
        
        return FeedbackStats(
            total_feedback=row['total_feedback'],
            good_count=row['good_count'],
            average_count=row['average_count'],
            bad_count=row['bad_count'],
            good_percentage=float(row['good_percentage'] or 0),
            average_percentage=float((row['average_count'] or 0) * 100.0 / (row['total_feedback'] or 1)),
            bad_percentage=float((row['bad_count'] or 0) * 100.0 / (row['total_feedback'] or 1)),
            total_with_suggestions=row['suggestion_count'],
            suggestion_rate=float((row['suggestion_count'] or 0) * 100.0 / (row['total_feedback'] or 1))
        )
    
    def get_daily_feedback_summary(self, days: int = 7) -> List[Dict]:
        """
        Get daily feedback summary for the last N days
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of daily summaries
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM daily_feedback_summary
            WHERE feedback_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY feedback_date DESC, rating
        """, (days,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_feedback_with_context(self, limit: int = 100) -> List[Dict]:
        """
        Get feedback with full conversation context
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of feedback records with context
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM feedback_with_context
            LIMIT %s
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_suggestions_by_rating(self, rating: str) -> List[str]:
        """
        Get all textual suggestions for a specific rating
        
        Args:
            rating: Rating to filter by ('bad', 'average', 'good')
            
        Returns:
            List of suggestions
        """
        if rating not in self.VALID_RATINGS:
            raise ValueError(f"Invalid rating. Must be one of: {', '.join(self.VALID_RATINGS)}")
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT suggestion, submitted_at
            FROM conversation_feedback
            WHERE rating = %s 
              AND has_suggestion = TRUE
              AND suggestion IS NOT NULL
            ORDER BY submitted_at DESC
        """, (rating,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def export_feedback_for_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_suggestions_only: bool = False
    ) -> List[Dict]:
        """
        Export feedback data for external analysis
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            include_suggestions_only: Only include feedback with suggestions
            
        Returns:
            List of feedback records
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                cf.id,
                cf.rating,
                cf.suggestion,
                cf.has_suggestion,
                cf.submitted_at,
                cf.total_messages_in_conversation,
                cf.conversation_duration_seconds,
                c.student_type,
                c.student_level,
                c.programs_discussed,
                c.lead_captured,
                c.safety_incidents_count
            FROM conversation_feedback cf
            JOIN conversations c ON cf.conversation_id = c.id
            WHERE 1=1
        """
        
        params = []
        
        if start_date:
            query += " AND cf.submitted_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND cf.submitted_at <= %s"
            params.append(end_date)
        
        if include_suggestions_only:
            query += " AND cf.has_suggestion = TRUE"
        
        query += " ORDER BY cf.submitted_at DESC"
        
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]


# ============================================
# FEEDBACK ANALYTICS
# ============================================

class FeedbackAnalytics:
    """
    Advanced analytics for feedback data
    """
    
    def __init__(self, db_connection):
        """
        Initialize analytics
        
        Args:
            db_connection: PostgreSQL connection
        """
        self.conn = db_connection
    
    def get_rating_distribution(self) -> Dict[str, int]:
        """
        Get distribution of ratings
        
        Returns:
            Dictionary with rating counts
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT rating, COUNT(*) as count
            FROM conversation_feedback
            GROUP BY rating
            ORDER BY rating
        """)
        
        return {row['rating']: row['count'] for row in cursor.fetchall()}
    
    def get_feedback_trends(self, days: int = 30) -> List[Dict]:
        """
        Get feedback trends over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of daily trends
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                DATE(submitted_at) as date,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE rating = 'good') as good,
                COUNT(*) FILTER (WHERE rating = 'average') as average,
                COUNT(*) FILTER (WHERE rating = 'bad') as bad,
                ROUND(100.0 * COUNT(*) FILTER (WHERE rating = 'good') / COUNT(*), 2) as good_pct
            FROM conversation_feedback
            WHERE submitted_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(submitted_at)
            ORDER BY date DESC
        """, (days,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_common_issues(self, rating: str = 'bad', limit: int = 10) -> List[str]:
        """
        Extract common issues from suggestions
        
        Args:
            rating: Rating to analyze
            limit: Number of suggestions to return
            
        Returns:
            List of suggestions
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT suggestion
            FROM conversation_feedback
            WHERE rating = %s 
              AND has_suggestion = TRUE
              AND suggestion IS NOT NULL
            ORDER BY submitted_at DESC
            LIMIT %s
        """, (rating, limit))
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_satisfaction_by_student_type(self) -> List[Dict]:
        """
        Get satisfaction scores by student type
        
        Returns:
            List of satisfaction by student type
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                c.student_type,
                COUNT(*) as total_feedback,
                COUNT(*) FILTER (WHERE cf.rating = 'good') as good_count,
                ROUND(100.0 * COUNT(*) FILTER (WHERE cf.rating = 'good') / COUNT(*), 2) as satisfaction_rate
            FROM conversation_feedback cf
            JOIN conversations c ON cf.conversation_id = c.id
            WHERE c.student_type IS NOT NULL
            GROUP BY c.student_type
            ORDER BY satisfaction_rate DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    """
    Example usage of feedback system
    """
    
    print("Feedback System Module Loaded!")
    print("\n✅ Features:")
    print("  • 3-level rating system (bad, average, good)")
    print("  • Optional textual suggestions")
    print("  • Automatic conversation flagging")
    print("  • Analytics and reporting")
    print("  • Trend analysis")
    print("\n✅ Usage:")
    print("  feedback_manager = FeedbackManager(db_connection)")
    print("  feedback_manager.submit_feedback(")
    print("      conversation_id=123,")
    print("      session_id='session_abc',")
    print("      rating='good',")
    print("      suggestion='Great responses!'")
    print("  )")
