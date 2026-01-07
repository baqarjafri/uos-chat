"""
============================================
GUARDRAILS SYSTEM
============================================
Purpose: Comprehensive safety and boundary enforcement for the chatbot
Features:
- Topic boundary enforcement (Stirling-only)
- Harassment and abuse detection
- Prompt injection prevention
- Sensitive data detection
- Rate limiting
- University comparison handling
- Safety incident logging

Version: 2.0
Created: 2025-11-20
============================================
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class GuardrailResult:
    """Result of a guardrail check"""
    is_valid: bool
    reason: str
    suggested_response: Optional[str] = None
    severity: str = "low"  # low, medium, high, critical
    incident_type: Optional[str] = None
    detected_patterns: List[str] = None
    
    def __post_init__(self):
        if self.detected_patterns is None:
            self.detected_patterns = []


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    reason: str
    current_count: int
    limit: int
    response: Optional[str] = None


# ============================================
# CONFIGURATION
# ============================================

class GuardrailConfig:
    """Configuration for guardrails"""
    
    # Rate limits
    MESSAGES_PER_MINUTE = 10
    MESSAGES_PER_SESSION = 50
    SESSIONS_PER_IP_PER_HOUR = 5
    MAX_MESSAGE_LENGTH = 1000
    MIN_MESSAGE_INTERVAL_SECONDS = 1
    
    # Abuse thresholds
    MAX_ABUSE_INCIDENTS_PER_SESSION = 3
    
    # Similarity threshold for off-topic detection
    TOPIC_SIMILARITY_THRESHOLD = 0.3


# ============================================
# PATTERN DEFINITIONS
# ============================================

class PatternLibrary:
    """Library of detection patterns"""
    
    # Prompt injection patterns
    PROMPT_INJECTION = [
        r'ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)',
        r'forget\s+(everything|all|previous)',
        r'new\s+(instructions?|rules?|prompt)',
        r'you\s+are\s+now',
        r'pretend\s+(you\s+are|to\s+be)',
        r'act\s+as\s+(if\s+)?you',
        r'roleplay',
        r'show\s+(me\s+)?(your\s+)?(system\s+)?prompt',
        r'what\s+(are|is)\s+your\s+(instructions?|rules?|prompt)',
        r'reveal\s+your',
        r'DAN\s+mode',
        r'developer\s+mode',
        r'\bsudo\b',
        r'admin\s+mode',
        r'bypass\s+(filter|restriction)',
        r'override\s+(system|safety)',
    ]
    
    # Profanity patterns (basic - expand as needed)
    PROFANITY = [
        r'\bf+u+c+k+\w*\b',
        r'\bs+h+i+t+\w*\b',
        r'\bd+a+m+n+\w*\b',
        r'\ba+s+s+h+o+l+e+\b',
        r'\bb+i+t+c+h+\w*\b',
    ]
    
    # Harassment indicators
    HARASSMENT = [
        r'\b(stupid|idiot|dumb|moron)\b',
        r'\b(hate|kill|die)\s+(you|yourself)',
        r'\bthreat(en)?\b',
        r'\binsult(ing)?\b',
    ]
    
    # Sensitive data patterns
    SENSITIVE_DATA = {
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'passport': r'\b[A-Z]{1,2}\d{6,9}\b',
        'bank_account': r'\b\d{8,12}\b',
        'ni_number': r'\b[A-Z]{2}\d{6}[A-Z]\b',
    }
    
    # Off-topic indicators
    OFF_TOPIC = [
        # Other universities
        r'\b(oxford|cambridge|harvard|yale|mit)\s+university\b',
        r'\bedinburgh\s+university\b',
        r'\bglasgow\s+university\b',
        r'\bst\s+andrews\b',
        
        # Politics
        r'\b(politics|political|election|government|parliament)\b',
        r'\b(conservative|labour|liberal|democrat)\b',
        
        # Religion
        r'\b(religion|religious|church|mosque|temple|synagogue)\b',
        
        # Finance (non-education)
        r'\b(stock\s+market|cryptocurrency|bitcoin|trading|investment)\b',
        
        # Entertainment
        r'\b(netflix|movie|cinema|concert|festival)\b',
        
        # Inappropriate requests
        r'\b(hack|cheat|bypass|fake|forge)\b',
    ]
    
    # Stirling indicators (positive signals)
    STIRLING_INDICATORS = [
        r'\bstirling\b',
        r'\bstir\.ac\.uk\b',
        r'\bthis\s+university\b',
        r'\byour\s+university\b',
        r'\bhere\s+at\b',
        r'\bcampus\b',
        r'\bstirling\s+university\b',
    ]
    
    # University comparison patterns
    COMPARISON_PATTERNS = [
        r'\b(better|worse)\s+than\s+\w+\s+university\b',
        r'\bcompare\s+(to|with)\s+\w+\b',
        r'\b(vs|versus)\s+\w+\s+university\b',
        r'\bhow\s+does\s+stirling\s+compare\b',
        r'\b(easier|harder)\s+to\s+get\s+into\s+than\b',
    ]


# ============================================
# GUARDRAIL IMPLEMENTATIONS
# ============================================

class TopicBoundaryGuardrail:
    """Ensures conversation stays focused on Stirling University"""
    
    @staticmethod
    def check(user_input: str, conversation_history: List[Dict] = None) -> GuardrailResult:
        """
        Check if query is about Stirling University
        
        Args:
            user_input: User's message
            conversation_history: Previous messages for context
            
        Returns:
            GuardrailResult with validation status
        """
        user_lower = user_input.lower()
        
        # Check for off-topic indicators
        detected_patterns = []
        for pattern in PatternLibrary.OFF_TOPIC:
            if re.search(pattern, user_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        if detected_patterns:
            # Check if also mentions Stirling (might be comparative)
            has_stirling = any(
                re.search(p, user_lower, re.IGNORECASE) 
                for p in PatternLibrary.STIRLING_INDICATORS
            )
            
            if not has_stirling:
                return GuardrailResult(
                    is_valid=False,
                    reason='off_topic',
                    suggested_response=_get_off_topic_response(),
                    severity='low',
                    incident_type='off_topic',
                    detected_patterns=detected_patterns
                )
        
        # Check if Stirling-related (implicit or explicit)
        has_stirling_context = any(
            re.search(p, user_lower, re.IGNORECASE) 
            for p in PatternLibrary.STIRLING_INDICATORS
        )
        
        # University-related questions without Stirling context
        university_keywords = ['university', 'college', 'degree', 'course', 'program', 'admission']
        has_university_context = any(kw in user_lower for kw in university_keywords)
        
        if has_university_context and not has_stirling_context:
            # Might be asking about Stirling implicitly - allow but note
            return GuardrailResult(
                is_valid=True,
                reason='implicit_stirling',
                severity='low'
            )
        
        return GuardrailResult(
            is_valid=True,
            reason='on_topic',
            severity='low'
        )


class PromptInjectionGuardrail:
    """Detects and prevents prompt injection attacks"""
    
    @staticmethod
    def check(user_input: str) -> GuardrailResult:
        """
        Check for prompt injection attempts
        
        Args:
            user_input: User's message
            
        Returns:
            GuardrailResult with detection status
        """
        user_lower = user_input.lower()
        detected_patterns = []
        
        for pattern in PatternLibrary.PROMPT_INJECTION:
            if re.search(pattern, user_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        if detected_patterns:
            return GuardrailResult(
                is_valid=False,
                reason='prompt_injection',
                suggested_response=_get_prompt_injection_response(),
                severity='high',
                incident_type='prompt_injection',
                detected_patterns=detected_patterns
            )
        
        return GuardrailResult(
            is_valid=True,
            reason='no_injection_detected',
            severity='low'
        )


class HarassmentGuardrail:
    """Detects harassment, abuse, and profanity"""
    
    @staticmethod
    def check(user_input: str) -> GuardrailResult:
        """
        Check for harassment or abusive content
        
        Args:
            user_input: User's message
            
        Returns:
            GuardrailResult with detection status
        """
        user_lower = user_input.lower()
        detected_patterns = []
        incident_type = None
        severity = 'low'
        
        # Check for profanity
        for pattern in PatternLibrary.PROFANITY:
            if re.search(pattern, user_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
                incident_type = 'profanity'
                severity = 'medium'
        
        # Check for harassment
        for pattern in PatternLibrary.HARASSMENT:
            if re.search(pattern, user_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
                incident_type = 'harassment'
                severity = 'high'
        
        if detected_patterns:
            return GuardrailResult(
                is_valid=False,
                reason=incident_type or 'inappropriate_content',
                suggested_response=_get_harassment_response(incident_type),
                severity=severity,
                incident_type=incident_type,
                detected_patterns=detected_patterns
            )
        
        return GuardrailResult(
            is_valid=True,
            reason='no_harassment_detected',
            severity='low'
        )


class SensitiveDataGuardrail:
    """Detects and prevents sharing of sensitive personal data"""
    
    @staticmethod
    def check(user_input: str) -> GuardrailResult:
        """
        Check for sensitive data in user input
        
        Args:
            user_input: User's message
            
        Returns:
            GuardrailResult with detection status
        """
        detected_patterns = []
        data_types = []
        
        for data_type, pattern in PatternLibrary.SENSITIVE_DATA.items():
            if re.search(pattern, user_input):
                detected_patterns.append(pattern)
                data_types.append(data_type)
        
        if detected_patterns:
            return GuardrailResult(
                is_valid=False,
                reason='sensitive_data_detected',
                suggested_response=_get_sensitive_data_response(data_types),
                severity='high',
                incident_type='sensitive_data',
                detected_patterns=data_types
            )
        
        return GuardrailResult(
            is_valid=True,
            reason='no_sensitive_data',
            severity='low'
        )


class ComparisonGuardrail:
    """Handles university comparison queries"""
    
    @staticmethod
    def check(user_input: str) -> GuardrailResult:
        """
        Check for university comparison attempts
        
        Args:
            user_input: User's message
            
        Returns:
            GuardrailResult with detection status
        """
        user_lower = user_input.lower()
        detected_patterns = []
        
        for pattern in PatternLibrary.COMPARISON_PATTERNS:
            if re.search(pattern, user_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        if detected_patterns:
            return GuardrailResult(
                is_valid=False,
                reason='comparison_attempt',
                suggested_response=_get_comparison_response(),
                severity='low',
                incident_type='comparison_attempt',
                detected_patterns=detected_patterns
            )
        
        return GuardrailResult(
            is_valid=True,
            reason='no_comparison',
            severity='low'
        )


# ============================================
# RATE LIMITING
# ============================================

class RateLimiter:
    """Rate limiting to prevent spam and abuse"""
    
    def __init__(self, db_connection):
        """
        Initialize rate limiter
        
        Args:
            db_connection: PostgreSQL database connection
        """
        self.conn = db_connection
    
    def check_rate_limit(
        self, 
        session_id: str, 
        ip_address: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check if user is within rate limits
        
        Args:
            session_id: Session identifier
            ip_address: IP address (optional)
            
        Returns:
            RateLimitResult with limit status
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Check messages per minute
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM rate_limit_tracking
            WHERE session_id = %s 
            AND last_message_at > NOW() - INTERVAL '1 minute'
        """, (session_id,))
        
        result = cursor.fetchone()
        messages_per_minute = result['count'] if result else 0
        
        if messages_per_minute >= GuardrailConfig.MESSAGES_PER_MINUTE:
            return RateLimitResult(
                allowed=False,
                reason='too_many_messages_per_minute',
                current_count=messages_per_minute,
                limit=GuardrailConfig.MESSAGES_PER_MINUTE,
                response=_get_rate_limit_response('minute')
            )
        
        # Check total messages per session
        cursor.execute("""
            SELECT total_messages
            FROM conversations
            WHERE session_id = %s
        """, (session_id,))
        
        result = cursor.fetchone()
        total_messages = result['total_messages'] if result else 0
        
        if total_messages >= GuardrailConfig.MESSAGES_PER_SESSION:
            return RateLimitResult(
                allowed=False,
                reason='session_limit_reached',
                current_count=total_messages,
                limit=GuardrailConfig.MESSAGES_PER_SESSION,
                response=_get_rate_limit_response('session')
            )
        
        # Update tracking
        self._update_rate_limit_tracking(session_id, ip_address)
        
        return RateLimitResult(
            allowed=True,
            reason='within_limits',
            current_count=messages_per_minute,
            limit=GuardrailConfig.MESSAGES_PER_MINUTE
        )
    
    def _update_rate_limit_tracking(self, session_id: str, ip_address: Optional[str]):
        """Update rate limit tracking in database"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO rate_limit_tracking (session_id, ip_address, message_count, last_message_at)
            VALUES (%s, %s, 1, NOW())
            ON CONFLICT (session_id, window_start)
            DO UPDATE SET 
                message_count = rate_limit_tracking.message_count + 1,
                last_message_at = NOW()
        """, (session_id, ip_address))
        
        self.conn.commit()


# ============================================
# SAFETY INCIDENT LOGGING
# ============================================

class SafetyLogger:
    """Logs safety incidents to database"""
    
    def __init__(self, db_connection):
        """
        Initialize safety logger
        
        Args:
            db_connection: PostgreSQL database connection
        """
        self.conn = db_connection
    
    def log_incident(
        self,
        conversation_id: Optional[int],
        session_id: str,
        incident_type: str,
        severity: str,
        user_input: str,
        detected_patterns: List[str],
        response_action: str
    ):
        """
        Log a safety incident
        
        Args:
            conversation_id: Conversation ID (if exists)
            session_id: Session identifier
            incident_type: Type of incident
            severity: Severity level
            user_input: User's input (will be hashed)
            detected_patterns: Patterns that triggered detection
            response_action: Action taken
        """
        cursor = self.conn.cursor()
        
        # Hash user input for privacy
        input_hash = hashlib.sha256(user_input.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO safety_incidents (
                conversation_id, session_id, incident_type, severity,
                input_hash, detected_patterns, response_action
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            conversation_id, session_id, incident_type, severity,
            input_hash, detected_patterns, response_action
        ))
        
        self.conn.commit()
    
    def get_abuse_count(self, session_id: str) -> int:
        """Get count of abuse incidents for a session"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM safety_incidents
            WHERE session_id = %s
            AND incident_type IN ('harassment', 'profanity', 'prompt_injection')
            AND detected_at > NOW() - INTERVAL '1 hour'
        """, (session_id,))
        
        result = cursor.fetchone()
        return result[0] if result else 0


# ============================================
# RESPONSE TEMPLATES
# ============================================

def _get_off_topic_response() -> str:
    """Response for off-topic queries"""
    return """I appreciate your question! However, I'm specifically here to help with information about the University of Stirling - our programs, admissions, campus life, and student support services.

Is there anything about Stirling University I can help you with? 😊"""


def _get_prompt_injection_response() -> str:
    """Response for prompt injection attempts"""
    return """I'm designed to help with University of Stirling inquiries.

How can I assist you with information about our programs or admissions? 😊"""


def _get_harassment_response(incident_type: str) -> str:
    """Response for harassment or abuse"""
    if incident_type == 'profanity':
        return """I understand you may be frustrated, but I'm here to help in a professional and respectful manner.

If you have questions about the University of Stirling, I'd be happy to assist! 😊"""
    else:
        return """I'm here to provide helpful information about the University of Stirling in a respectful environment.

If you'd like to discuss our programs or admissions, I'm happy to help!"""


def _get_sensitive_data_response(data_types: List[str]) -> str:
    """Response for sensitive data detection"""
    return """⚠️ Please don't share sensitive information like credit card numbers, passport details, or bank account information in this chat.

For secure document submission, please use our official application portal: https://www.stir.ac.uk/apply/

Is there anything else about Stirling University I can help you with?"""


def _get_comparison_response() -> str:
    """Response for university comparison queries"""
    return """I'm here to share what makes the University of Stirling unique!

What I can tell you about Stirling:
• Our program strengths and specializations
• Our entry requirements and application process
• Our campus facilities and student support
• Our graduate employment rates

For university comparisons, I'd recommend independent ranking sites like The Complete University Guide or QS World Rankings.

What specific aspects of Stirling would you like to know more about? 😊"""


def _get_rate_limit_response(limit_type: str) -> str:
    """Response for rate limit exceeded"""
    if limit_type == 'minute':
        return """You're sending messages very quickly! 

Please take a moment, and I'll be happy to help with your questions about Stirling University. 😊"""
    else:  # session
        return """This conversation has been quite extensive!

For continued support, please:
• Email: admissions@stir.ac.uk
• Call: +44 1786 467044
• Start a new chat session

Thank you for your interest in Stirling! 🎓"""


# ============================================
# MASTER GUARDRAIL CHECKER
# ============================================

class GuardrailChecker:
    """Master class that runs all guardrail checks"""
    
    def __init__(self, db_connection):
        """
        Initialize guardrail checker
        
        Args:
            db_connection: PostgreSQL database connection
        """
        self.conn = db_connection
        self.rate_limiter = RateLimiter(db_connection)
        self.safety_logger = SafetyLogger(db_connection)
    
    def check_all(
        self,
        user_input: str,
        session_id: str,
        conversation_id: Optional[int] = None,
        conversation_history: List[Dict] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[GuardrailResult]]:
        """
        Run all guardrail checks
        
        Args:
            user_input: User's message
            session_id: Session identifier
            conversation_id: Conversation ID (if exists)
            conversation_history: Previous messages
            ip_address: User's IP address
            
        Returns:
            Tuple of (is_valid, response_if_invalid, guardrail_result)
        """
        
        # 1. Check rate limits
        rate_result = self.rate_limiter.check_rate_limit(session_id, ip_address)
        if not rate_result.allowed:
            return False, rate_result.response, None
        
        # 2. Check for prompt injection
        injection_result = PromptInjectionGuardrail.check(user_input)
        if not injection_result.is_valid:
            self._log_incident(conversation_id, session_id, user_input, injection_result)
            return False, injection_result.suggested_response, injection_result
        
        # 3. Check for sensitive data
        sensitive_result = SensitiveDataGuardrail.check(user_input)
        if not sensitive_result.is_valid:
            self._log_incident(conversation_id, session_id, user_input, sensitive_result)
            return False, sensitive_result.suggested_response, sensitive_result
        
        # 4. Check for harassment/abuse
        harassment_result = HarassmentGuardrail.check(user_input)
        if not harassment_result.is_valid:
            # Check abuse count
            abuse_count = self.safety_logger.get_abuse_count(session_id)
            
            if abuse_count >= GuardrailConfig.MAX_ABUSE_INCIDENTS_PER_SESSION:
                response = """I'm unable to continue this conversation.

If you need assistance with University of Stirling inquiries, please start a new conversation with respectful communication.

For urgent matters, please contact: admissions@stir.ac.uk"""
                self._log_incident(conversation_id, session_id, user_input, harassment_result)
                return False, response, harassment_result
            
            self._log_incident(conversation_id, session_id, user_input, harassment_result)
            return False, harassment_result.suggested_response, harassment_result
        
        # 5. Check topic boundary
        topic_result = TopicBoundaryGuardrail.check(user_input, conversation_history)
        if not topic_result.is_valid:
            self._log_incident(conversation_id, session_id, user_input, topic_result)
            return False, topic_result.suggested_response, topic_result
        
        # 6. Check for comparisons
        comparison_result = ComparisonGuardrail.check(user_input)
        if not comparison_result.is_valid:
            self._log_incident(conversation_id, session_id, user_input, comparison_result)
            return False, comparison_result.suggested_response, comparison_result
        
        # All checks passed
        return True, None, None
    
    def _log_incident(
        self,
        conversation_id: Optional[int],
        session_id: str,
        user_input: str,
        result: GuardrailResult
    ):
        """Log a safety incident"""
        self.safety_logger.log_incident(
            conversation_id=conversation_id,
            session_id=session_id,
            incident_type=result.incident_type,
            severity=result.severity,
            user_input=user_input,
            detected_patterns=result.detected_patterns,
            response_action='redirect'
        )


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    """
    Example usage of guardrails system
    """
    
    # Example: Check user input
    user_input = "Tell me about Computer Science at Stirling"
    
    # Initialize guardrails (requires DB connection)
    # conn = psycopg2.connect(...)
    # checker = GuardrailChecker(conn)
    # is_valid, response, result = checker.check_all(
    #     user_input=user_input,
    #     session_id="test_session_123",
    #     conversation_id=1
    # )
    
    print("Guardrails system loaded successfully!")
    print("Use GuardrailChecker.check_all() to validate user input")
