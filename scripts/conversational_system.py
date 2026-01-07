"""
============================================
CONVERSATIONAL RAG SYSTEM - LANGGRAPH
============================================
Purpose: Complete 3-agent conversational system with guardrails
Architecture:
- Agent 1: Router (intent classification, student detection, guardrails)
- Agent 2: RAG (enhanced search, answer generation)
- Agent 3: Lead Capture (natural data collection, email sending)

Version: 2.0
Created: 2025-11-20
============================================
"""

import os
import re
import uuid
from datetime import datetime
from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add

import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
import anthropic

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Import our custom modules
from scripts.guardrails import GuardrailChecker
from scripts.enhanced_rag import EnhancedRAG
from scripts.feedback_system import FeedbackManager
from scripts.lead_manager import LeadManager, LeadData, should_ask_for_name, personalize_response


# ============================================
# STATE DEFINITION
# ============================================

class ConversationState(TypedDict):
    """State schema for the conversation"""
    
    # Session identifiers
    session_id: str
    conversation_id: Optional[int]
    ip_address: Optional[str]
    
    # Messages
    messages: Annotated[List[BaseMessage], add]
    user_input: str
    conversation_history: List[Dict]
    
    # Intent classification
    intent: Optional[str]
    confidence: float
    needs_clarification: bool
    clarification_context: Optional[str]
    
    # Student profile (detected during conversation)
    student_type: Optional[str]  # scottish, uk, eu, international, unknown
    student_level: Optional[str]  # undergraduate, postgraduate, phd, unknown
    detected_programs: List[str]
    detected_location: Optional[str]
    
    # RAG results
    search_results: Optional[List[Dict]]
    reranked_results: Optional[List[Dict]]
    answer: Optional[str]
    sources: List[str]
    search_quality_score: float
    
    # Lead capture
    lead_captured: bool
    lead_data: Optional[Dict]
    ready_for_lead_capture: bool
    
    # Progressive lead capture (new)
    user_name: Optional[str]  # For personalization
    name_asked: bool  # Whether we've asked for name
    lead_capture_completeness: int  # 0-100 score
    
    # Control flow
    next_action: str
    turn_count: int
    guardrail_triggered: bool
    guardrail_response: Optional[str]
    
    # Metadata
    processing_start_time: Optional[datetime]
    processing_time_ms: Optional[int]


# ============================================
# AGENT 1: ROUTER
# ============================================

class RouterAgent:
    """
    Router Agent - Intent classification, student detection, and guardrails
    """
    
    def __init__(
        self,
        db_connection,
        openai_client: OpenAI,
        guardrail_checker: GuardrailChecker
    ):
        """
        Initialize router agent
        
        Args:
            db_connection: PostgreSQL connection
            openai_client: OpenAI client
            guardrail_checker: Guardrail checker instance
        """
        self.conn = db_connection
        self.openai_client = openai_client
        self.guardrails = guardrail_checker
    
    def __call__(self, state: ConversationState) -> ConversationState:
        """
        Process user input through router
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with routing decision
        """
        user_input = state["user_input"]
        session_id = state["session_id"]
        conversation_id = state.get("conversation_id")
        conversation_history = state.get("conversation_history", [])
        ip_address = state.get("ip_address")
        
        # 1. Run guardrails
        is_valid, guardrail_response, guardrail_result = self.guardrails.check_all(
            user_input=user_input,
            session_id=session_id,
            conversation_id=conversation_id,
            conversation_history=conversation_history,
            ip_address=ip_address
        )
        
        if not is_valid:
            # Guardrail triggered - return with response
            return {
                **state,
                "guardrail_triggered": True,
                "guardrail_response": guardrail_response,
                "answer": guardrail_response,
                "next_action": "end"
            }
        
        # 2. Detect student type and location
        student_type, detected_location = self._detect_student_type(user_input, conversation_history)
        
        # 3. Detect student level
        student_level = self._detect_student_level(user_input, conversation_history)
        
        # 4. Detect programs mentioned
        detected_programs = self._detect_programs(user_input)
        
        # 5. Classify intent (pass conversation history to avoid false greeting detection)
        intent, confidence = self._classify_intent(user_input, conversation_history)
        
        # 6. Check if ready for lead capture
        ready_for_lead_capture = self._check_lead_capture_readiness(
            state, intent, conversation_history
        )
        
        # 7. Determine next action
        if ready_for_lead_capture and not state.get("lead_captured", False):
            next_action = "lead_capture"
        elif intent in ["program_inquiry", "fee_question", "requirement_question", "general_question"]:
            next_action = "rag"
        elif intent == "greeting":
            next_action = "greeting"
        else:
            next_action = "rag"  # Default to RAG
        
        # Update state
        return {
            **state,
            "intent": intent,
            "confidence": confidence,
            "student_type": student_type or state.get("student_type"),
            "student_level": student_level or state.get("student_level"),
            "detected_location": detected_location or state.get("detected_location"),
            "detected_programs": list(set(
                state.get("detected_programs", []) + detected_programs
            )),
            "ready_for_lead_capture": ready_for_lead_capture,
            "next_action": next_action,
            "guardrail_triggered": False,
            "turn_count": state.get("turn_count", 0) + 1
        }
    
    def _detect_student_type(
        self,
        user_input: str,
        conversation_history: List[Dict]
    ) -> tuple[Optional[str], Optional[str]]:
        """Detect student type from location mentions"""
        user_lower = user_input.lower()
        
        # Scottish indicators
        scottish_locations = [
            'scotland', 'scottish', 'edinburgh', 'glasgow', 'aberdeen',
            'dundee', 'stirling', 'inverness', 'perth'
        ]
        if any(loc in user_lower for loc in scottish_locations):
            return 'scottish', user_input
        
        # UK indicators
        uk_locations = [
            'england', 'wales', 'northern ireland', 'london', 'manchester',
            'birmingham', 'liverpool', 'leeds', 'bristol', 'newcastle'
        ]
        if any(loc in user_lower for loc in uk_locations):
            return 'uk', user_input
        
        # International indicators (common countries)
        international_indicators = [
            'nigeria', 'india', 'pakistan', 'china', 'usa', 'america',
            'canada', 'australia', 'kenya', 'ghana', 'zimbabwe'
        ]
        if any(country in user_lower for country in international_indicators):
            return 'international', user_input
        
        # Check for "I'm from" pattern
        from_match = re.search(r"i'?m from (\w+)", user_lower)
        if from_match:
            location = from_match.group(1)
            return 'unknown', location
        
        return None, None
    
    def _detect_student_level(
        self,
        user_input: str,
        conversation_history: List[Dict]
    ) -> Optional[str]:
        """Detect student level from query"""
        user_lower = user_input.lower()
        
        # Undergraduate indicators
        ug_indicators = ['undergraduate', 'bachelor', 'bsc', 'ba', 'beng', 'ug']
        if any(ind in user_lower for ind in ug_indicators):
            return 'undergraduate'
        
        # Postgraduate indicators
        pg_indicators = ['postgraduate', 'master', 'msc', 'ma', 'pg', 'taught']
        if any(ind in user_lower for ind in pg_indicators):
            return 'postgraduate'
        
        # PhD indicators
        phd_indicators = ['phd', 'doctorate', 'doctoral', 'research degree']
        if any(ind in user_lower for ind in phd_indicators):
            return 'phd'
        
        return None
    
    def _detect_programs(self, user_input: str) -> List[str]:
        """Detect program names mentioned"""
        user_lower = user_input.lower()
        programs = []
        
        # Common program patterns
        program_patterns = {
            'computer science': r'\b(computer science|computing|cs)\b',
            'artificial intelligence': r'\b(artificial intelligence|ai|machine learning)\b',
            'data science': r'\b(data science|data analytics)\b',
            'business management': r'\b(business management|business|management)\b',
            'psychology': r'\b(psychology)\b',
            'nursing': r'\b(nursing)\b',
            'education': r'\b(education|teaching)\b',
            'law': r'\b(law|legal)\b',
        }
        
        for program, pattern in program_patterns.items():
            if re.search(pattern, user_lower):
                programs.append(program)
        
        return programs
    
    def _classify_intent(self, user_input: str, conversation_history: List[Dict] = None) -> tuple[str, float]:
        """Classify user intent"""
        user_lower = user_input.lower()
        
        # Only classify as greeting if it's JUST a greeting (no other content) 
        # AND it's a very short message (to avoid false positives)
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'greetings']
        if len(user_input.split()) <= 3:  # Only short messages
            if any(user_lower.strip() == word or user_lower.strip() == word + '!' for word in greeting_words):
                # Only return greeting if there's no conversation history
                if not conversation_history or len(conversation_history) == 0:
                    return 'greeting', 0.9
        
        # All other intents
        if any(word in user_lower for word in ['fee', 'cost', 'tuition', 'price', 'how much']):
            return 'fee_question', 0.85
        
        if any(word in user_lower for word in ['requirement', 'entry', 'qualification', 'need', 'criteria']):
            return 'requirement_question', 0.85
        
        if any(word in user_lower for word in ['apply', 'application', 'deadline', 'when', 'how to']):
            return 'application_question', 0.85
        
        if any(word in user_lower for word in ['program', 'course', 'degree', 'study', 'major']):
            return 'program_inquiry', 0.8
        
        return 'general_question', 0.7
    
    def _check_lead_capture_readiness(
        self,
        state: ConversationState,
        intent: str,
        conversation_history: List[Dict]
    ) -> bool:
        """Check if conversation is ready for lead capture"""
        turn_count = state.get("turn_count", 0)
        
        # NEVER trigger lead capture on first few messages
        # User needs to have a conversation first before we ask for contact info
        if turn_count < 3:
            return False
        
        # ONLY ready after 8+ turns of substantive conversation
        # This ensures natural flow before asking for contact info
        if turn_count >= 8 and len(conversation_history) >= 16:
            # Check if user has shown genuine interest
            detected_programs = state.get("detected_programs", [])
            if len(detected_programs) >= 2:
                return True
        
        # Or ONLY if user explicitly requests contact (not just asking how to apply)
        user_input = state.get("user_input", "").lower()
        if any(phrase in user_input for phrase in [
            "send me information", "contact me", "email me details",
            "connect me with admissions", "speak to someone", "talk to a person"
        ]):
            return True
        
        return False


# ============================================
# AGENT 2: RAG
# ============================================

class RAGAgent:
    """
    RAG Agent - Enhanced search and answer generation
    """
    
    def __init__(self, enhanced_rag: EnhancedRAG):
        """
        Initialize RAG agent
        
        Args:
            enhanced_rag: EnhancedRAG instance
        """
        self.rag = enhanced_rag
    
    def __call__(self, state: ConversationState) -> ConversationState:
        """
        Process query through enhanced RAG
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with answer
        """
        # Handle greeting separately (only for first message)
        if state.get("intent") == "greeting" and len(state.get("conversation_history", [])) == 0:
            greeting_response = self._generate_greeting(state)
            return {
                **state,
                "answer": greeting_response,
                "next_action": "end"
            }
        
        # Build enhanced query by combining current input with full conversation context
        # This ensures follow-up questions include program names, student type, and topics
        enhanced_query = self._build_enhanced_query(state)
        
        # Query RAG system with enhanced query for better context retrieval
        rag_response = self.rag.query(
            query=enhanced_query,
            student_type=state.get("student_type"),
            student_level=state.get("student_level"),
            detected_programs=state.get("detected_programs", []),
            conversation_history=state.get("conversation_history", [])
        )
        
        return {
            **state,
            "answer": rag_response.answer,
            "sources": rag_response.sources,
            "search_quality_score": rag_response.search_quality_score,
            "needs_clarification": rag_response.needs_clarification,
            "clarification_context": rag_response.clarification_context,
            "next_action": "end"
        }
    
    def _build_enhanced_query(self, state: ConversationState) -> str:
        """
        Build an enhanced search query using ChatGPT-style context management:
        - Full conversation history (last N user messages)
        - Detected entities (level, location, nationality, programs)
        - Current question
        
        This ensures robust context retention for follow-up questions.
        """
        query_parts = []
        
        # 1. DETECTED ENTITIES - accumulated across conversation
        
        # 1a. Programs of interest
        detected_programs = state.get("detected_programs", [])
        if detected_programs:
            query_parts.extend(detected_programs)
        
        # 1b. Level of study (undergrad, postgrad, PhD, research, short courses)
        student_level = state.get("student_level")
        if student_level and student_level != "unknown":
            query_parts.append(student_level)
        
        # 1c. Student type / Nationality (scottish, uk, eu, international)
        student_type = state.get("student_type")
        if student_type and student_type != "unknown":
            query_parts.append(f"{student_type} student")
        
        # 1d. Current location / Detected location
        detected_location = state.get("detected_location")
        if detected_location:
            query_parts.append(detected_location)
        
        # 2. FULL CONVERSATION HISTORY - include last 3 user messages completely
        # This is the key fix: don't just extract keywords, include full context
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            # Extract last 3 user messages (full content, not just keywords)
            user_messages = [
                msg["content"] for msg in conversation_history
                if msg.get("role") == "user"
            ][-3:]  # Last 3 user messages
            query_parts.extend(user_messages)
        
        # 3. CURRENT QUESTION
        user_input = state.get("user_input", "")
        query_parts.append(user_input)
        
        # Join all parts (no dedup - we want full context)
        enhanced_query = " ".join(query_parts)
        
        return enhanced_query
    
    def _generate_greeting(self, state: ConversationState) -> str:
        """Generate friendly greeting with name personalization"""
        user_name = state.get("user_name")
        
        if user_name:
            # Personalized greeting if we have the name
            return f"""Hey {user_name}! 👋 Welcome to the University of Stirling!

I'm here to help with courses, admissions, fees, scholarships - anything you need. What would you like to know?"""
        else:
            # Ask for name in greeting (hybrid approach)
            return """Hey! 👋 Welcome to Stirling University! May I know your name?"""


# ============================================
# AGENT 3: LEAD CAPTURE
# ============================================

class LeadCaptureAgent:
    """
    Lead Capture Agent - Progressive lead capture with phone examples.
    Uses LeadManager for extraction and asks only for missing fields.
    """
    
    def __init__(self, db_connection):
        """
        Initialize lead capture agent
        
        Args:
            db_connection: PostgreSQL connection
        """
        self.conn = db_connection
        self.lead_manager = LeadManager(db_connection)
    
    def __call__(self, state: ConversationState) -> ConversationState:
        """
        Attempt to capture lead information progressively.
        Only asks for missing fields, includes phone format examples.
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with lead capture status
        """
        user_input = state["user_input"]
        conversation_history = state.get("conversation_history", [])
        user_name = state.get("user_name")
        
        # Build current lead data from state and extract from current message
        lead = LeadData(
            name=user_name,
            student_type=state.get("student_type"),
            student_level=state.get("student_level"),
            country=state.get("detected_location"),
            programs_interested=state.get("detected_programs", [])
        )
        
        # Extract any new info from current message
        lead = self.lead_manager.extract_from_message(user_input, lead)
        
        # Check if we have email (minimum for lead capture)
        if lead.email:
            # Extract conversation context for admissions team
            last_messages = self._get_last_messages(conversation_history, limit=5)
            user_query = self._extract_user_query(conversation_history)
            conversation_summary = self._generate_conversation_summary(conversation_history, state)
            escalation_reason = self._determine_escalation_reason(state, conversation_history)
            
            # Save lead with full context
            lead_id = self.lead_manager.save_lead_to_db(
                conversation_id=state["conversation_id"],
                lead=lead,
                user_query=user_query,
                conversation_summary=conversation_summary,
                escalation_reason=escalation_reason,
                last_messages=last_messages
            )
            
            name_to_use = lead.name or user_name or "there"
            response = f"""Thank you, {name_to_use}! 🎉

I've forwarded your query to our admissions team. Here's what they'll receive:

**Your query:** {user_query[:100]}{'...' if len(user_query) > 100 else ''}

They will contact you at **{lead.email}** within 1-2 business days with a personalized response.

Is there anything else I can help you with in the meantime?"""
            
            return {
                **state,
                "lead_captured": True,
                "lead_data": lead.to_dict(),
                "user_name": lead.name or user_name,
                "answer": response,
                "next_action": "end"
            }
        else:
            # User hasn't provided email yet - prompt for missing fields with examples
            name_to_use = lead.name or user_name or "there"
            
            # Build prompt asking only for what's missing
            missing_items = []
            
            if not lead.name and not user_name:
                missing_items.append("**Your name**")
            
            missing_items.append("**Your email address**")
            
            if not lead.phone:
                missing_items.append("Your phone number with **country code** (e.g., **+44** 7911 123456 for UK)")
            
            response = f"""Thanks {name_to_use}! I'd love to connect you with our admissions team for a detailed response.

Could you please share:
"""
            for item in missing_items:
                response += f"- {item}\n"
            
            response += "\nOur team will review your query and get back to you within 1-2 business days."
            
            return {
                **state,
                "lead_data": lead.to_dict(),
                "user_name": lead.name or user_name,
                "answer": response,
                "next_action": "end"
            }
    
    def _get_last_messages(self, conversation_history: List[Dict], limit: int = 5) -> List[Dict]:
        """Get the last N messages from conversation history"""
        if not conversation_history:
            return []
        return conversation_history[-limit:]
    
    def _extract_user_query(self, conversation_history: List[Dict]) -> str:
        """Extract the main user query that triggered escalation"""
        if not conversation_history:
            return "General inquiry"
        
        # Get the last few user messages to understand the query
        user_messages = [
            msg.get("content", "") 
            for msg in conversation_history 
            if msg.get("role") == "user"
        ]
        
        if user_messages:
            # Return the last user message as the primary query
            return user_messages[-1] if user_messages else "General inquiry"
        return "General inquiry"
    
    def _generate_conversation_summary(self, conversation_history: List[Dict], state: ConversationState) -> str:
        """Generate a summary of the conversation for admissions team"""
        summary_parts = []
        
        # Add detected programs
        programs = state.get("detected_programs", [])
        if programs:
            summary_parts.append(f"Programs discussed: {', '.join(programs)}")
        
        # Add student type if known
        student_type = state.get("student_type")
        if student_type and student_type != "unknown":
            summary_parts.append(f"Student type: {student_type}")
        
        # Add student level if known
        student_level = state.get("student_level")
        if student_level:
            summary_parts.append(f"Level: {student_level}")
        
        # Summarize user questions
        user_questions = [
            msg.get("content", "")[:100] 
            for msg in conversation_history 
            if msg.get("role") == "user"
        ][-3:]  # Last 3 questions
        
        if user_questions:
            summary_parts.append(f"User asked about: {'; '.join(user_questions)}")
        
        return " | ".join(summary_parts) if summary_parts else "General inquiry about University of Stirling"
    
    def _determine_escalation_reason(self, state: ConversationState, conversation_history: List[Dict]) -> str:
        """Determine why the query was escalated"""
        # Check the last assistant message for escalation indicators
        if conversation_history:
            last_assistant_msgs = [
                msg.get("content", "") 
                for msg in conversation_history 
                if msg.get("role") == "assistant"
            ]
            if last_assistant_msgs:
                last_response = last_assistant_msgs[-1].lower()
                
                if "application status" in last_response:
                    return "Application status inquiry - requires applicant portal access"
                elif "specific case" in last_response or "individual" in last_response:
                    return "Individual case inquiry - requires human review"
                elif "visa" in last_response:
                    return "Complex visa query - requires immigration advisor"
                elif "don't have" in last_response or "knowledge base" in last_response:
                    return "Information not in knowledge base"
        
        # Default based on intent
        intent = state.get("intent", "general")
        intent_reasons = {
            "application_question": "Application-related query requiring human support",
            "fee_question": "Complex fee inquiry requiring verification",
            "requirement_question": "Specific requirement clarification needed",
            "visa_question": "Visa/immigration query requiring specialist advice"
        }
        
        return intent_reasons.get(intent, "Query requires human support")
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def _extract_name(self, text: str, state: ConversationState) -> Optional[str]:
        """Extract name from text"""
        # Simple pattern: "my name is X" or "I'm X"
        name_patterns = [
            r"my name is ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            r"i'?m ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            r"this is ([A-Z][a-z]+(?: [A-Z][a-z]+)*)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_topics(self, state: ConversationState) -> List[str]:
        """Extract topics discussed from conversation"""
        topics = set()
        
        if state.get("intent"):
            intent_map = {
                'fee_question': 'fees',
                'requirement_question': 'requirements',
                'application_question': 'application',
                'program_inquiry': 'programs'
            }
            topics.add(intent_map.get(state["intent"], 'general'))
        
        return list(topics)
    
    def _save_lead(self, conversation_id: int, lead_data: Dict) -> int:
        """Save lead to database with full conversation context"""
        import json
        cursor = self.conn.cursor()
        
        # Convert last_messages to JSON string for JSONB column
        last_messages_json = json.dumps(lead_data.get("last_messages", []))
        
        cursor.execute("""
            INSERT INTO leads (
                conversation_id, name, email, location, student_type,
                student_level, programs_interested, topics_discussed,
                user_query, conversation_summary, escalation_reason, last_messages
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            conversation_id,
            lead_data["name"],
            lead_data["email"],
            lead_data.get("location"),
            lead_data.get("student_type"),
            lead_data.get("student_level"),
            lead_data.get("programs_interested", []),
            lead_data.get("topics_discussed", []),
            lead_data.get("user_query"),
            lead_data.get("conversation_summary"),
            lead_data.get("escalation_reason"),
            last_messages_json
        ))
        
        lead_id = cursor.fetchone()[0]
        
        # Update conversation
        cursor.execute("""
            UPDATE conversations
            SET lead_captured = TRUE, lead_id = %s
            WHERE id = %s
        """, (lead_id, conversation_id))
        
        self.conn.commit()
        
        return lead_id


# ============================================
# CONVERSATION MANAGER
# ============================================

class ConversationManager:
    """Manages conversation state and database persistence"""
    
    def __init__(self, db_connection):
        """
        Initialize conversation manager
        
        Args:
            db_connection: PostgreSQL connection
        """
        self.conn = db_connection
    
    def create_conversation(self, session_id: str) -> int:
        """Create new conversation in database"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (session_id)
            VALUES (%s)
            RETURNING id
        """, (session_id,))
        
        conversation_id = cursor.fetchone()[0]
        self.conn.commit()
        
        return conversation_id
    
    def save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        sources: List[str] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Save message to database"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO messages (
                conversation_id, role, content, intent, confidence,
                sources, processing_time_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            conversation_id, role, content, intent, confidence,
            sources or [], processing_time_ms
        ))
        
        self.conn.commit()
    
    def update_conversation_profile(
        self,
        conversation_id: int,
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        detected_location: Optional[str] = None,
        programs_discussed: List[str] = None
    ):
        """Update conversation profile"""
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if student_type:
            updates.append("student_type = %s")
            params.append(student_type)
        
        if student_level:
            updates.append("student_level = %s")
            params.append(student_level)
        
        if detected_location:
            updates.append("detected_location = %s")
            params.append(detected_location)
        
        if programs_discussed:
            updates.append("programs_discussed = %s")
            params.append(programs_discussed)
        
        if updates:
            params.append(conversation_id)
            query = f"""
                UPDATE conversations
                SET {', '.join(updates)}
                WHERE id = %s
            """
            cursor.execute(query, params)
            self.conn.commit()
    
    def get_session_from_db(self, session_id: str) -> Optional[Dict]:
        """
        Load existing session from database by session_id.
        This enables session persistence across backend restarts.
        
        Returns None if session doesn't exist in database.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get the most recent conversation for this session
        cursor.execute("""
            SELECT id, student_type, student_level, detected_location, programs_discussed,
                   lead_captured, user_name, name_asked, lead_capture_completeness
            FROM conversations
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (session_id,))
        
        conv = cursor.fetchone()
        if not conv:
            return None
        
        # Get all messages for this conversation
        cursor.execute("""
            SELECT role, content
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
        """, (conv['id'],))
        
        messages = [{"role": row['role'], "content": row['content']} for row in cursor.fetchall()]
        
        # Return session data in the same format as in-memory sessions
        return {
            "conversation_id": conv['id'],
            "messages": messages,
            "student_type": conv['student_type'],
            "student_level": conv['student_level'],
            "detected_location": conv['detected_location'],
            "detected_programs": conv['programs_discussed'] or [],
            "lead_captured": conv.get('lead_captured', False),
            # Progressive lead capture fields
            "user_name": conv.get('user_name'),
            "name_asked": conv.get('name_asked', False),
            "lead_capture_completeness": conv.get('lead_capture_completeness', 0)
        }


# ============================================
# LANGGRAPH WORKFLOW
# ============================================

def create_conversational_graph(
    db_connection,
    openai_api_key: str,
    anthropic_api_key: str
) -> StateGraph:
    """
    Create LangGraph workflow
    
    Args:
        db_connection: PostgreSQL connection
        openai_api_key: OpenAI API key
        anthropic_api_key: Anthropic API key
        
    Returns:
        Compiled StateGraph
    """
    # Initialize components
    openai_client = OpenAI(api_key=openai_api_key)
    anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    guardrail_checker = GuardrailChecker(db_connection)
    enhanced_rag = EnhancedRAG(db_connection, openai_api_key, anthropic_api_key)
    
    # Initialize agents
    router_agent = RouterAgent(db_connection, openai_client, guardrail_checker)
    rag_agent = RAGAgent(enhanced_rag)
    lead_capture_agent = LeadCaptureAgent(db_connection)
    
    # Create graph
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("router", router_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("lead_capture", lead_capture_agent)
    
    # Define routing logic
    def route_after_router(state: ConversationState) -> str:
        """Route after router agent"""
        if state.get("guardrail_triggered"):
            return END
        
        next_action = state.get("next_action", "rag")
        
        if next_action == "lead_capture":
            return "lead_capture"
        elif next_action == "rag" or next_action == "greeting":
            return "rag"
        else:
            return END
    
    # Add edges
    workflow.set_entry_point("router")
    workflow.add_conditional_edges("router", route_after_router)
    workflow.add_edge("rag", END)
    workflow.add_edge("lead_capture", END)
    
    return workflow.compile()


# ============================================
# MAIN CONVERSATION HANDLER
# ============================================

class ConversationalRAGSystem:
    """Main system orchestrating everything"""
    
    def __init__(
        self,
        db_connection_string: str,
        openai_api_key: str,
        anthropic_api_key: str
    ):
        """
        Initialize conversational RAG system
        
        Args:
            db_connection_string: PostgreSQL connection string
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
        """
        self.conn = psycopg2.connect(db_connection_string)
        self.conversation_manager = ConversationManager(self.conn)
        self.feedback_manager = FeedbackManager(self.conn)
        self.graph = create_conversational_graph(
            self.conn, openai_api_key, anthropic_api_key
        )
        
        # Session storage (in production, use Redis or similar)
        self.sessions = {}
    
    def chat(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict:
        """
        Process user message
        
        Args:
            user_input: User's message
            session_id: Session identifier (creates new if None)
            ip_address: User's IP address
            
        Returns:
            Response dictionary
        """
        # Create or retrieve session
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            # FIRST: Try to restore session from database (persistence across restarts)
            db_session = self.conversation_manager.get_session_from_db(session_id)
            
            if db_session:
                # Session found in DB - restore it to memory
                self.sessions[session_id] = db_session
            else:
                # New session - create fresh conversation in DB
                conversation_id = self.conversation_manager.create_conversation(session_id)
                self.sessions[session_id] = {
                    "conversation_id": conversation_id,
                    "messages": [],
                    "student_type": None,
                    "student_level": None,
                    "detected_programs": [],
                    "detected_location": None,
                    "lead_captured": False,
                    # Progressive lead capture fields
                    "user_name": None,
                    "name_asked": False,
                    "lead_capture_completeness": 0
                }
        
        session = self.sessions[session_id]
        
        # Build initial state
        initial_state = ConversationState(
            session_id=session_id,
            conversation_id=session["conversation_id"],
            ip_address=ip_address,
            messages=[HumanMessage(content=user_input)],
            user_input=user_input,
            conversation_history=session["messages"],
            intent=None,
            confidence=0.0,
            needs_clarification=False,
            clarification_context=None,
            student_type=session.get("student_type"),
            student_level=session.get("student_level"),
            detected_programs=session.get("detected_programs", []),
            detected_location=session.get("detected_location"),
            search_results=None,
            reranked_results=None,
            answer=None,
            sources=[],
            search_quality_score=0.0,
            lead_captured=session.get("lead_captured", False),
            lead_data=None,
            ready_for_lead_capture=False,
            # Progressive lead capture fields
            user_name=session.get("user_name"),
            name_asked=session.get("name_asked", False),
            lead_capture_completeness=session.get("lead_capture_completeness", 0),
            next_action="router",
            turn_count=len(session["messages"]) // 2,
            guardrail_triggered=False,
            guardrail_response=None,
            processing_start_time=datetime.now(),
            processing_time_ms=None
        )
        
        # Run through graph
        final_state = self.graph.invoke(initial_state)
        
        # Calculate processing time
        processing_time = (datetime.now() - initial_state["processing_start_time"]).total_seconds() * 1000
        
        # Save messages
        self.conversation_manager.save_message(
            conversation_id=session["conversation_id"],
            role="user",
            content=user_input,
            intent=final_state.get("intent"),
            confidence=final_state.get("confidence")
        )
        
        self.conversation_manager.save_message(
            conversation_id=session["conversation_id"],
            role="assistant",
            content=final_state["answer"],
            sources=final_state.get("sources", []),
            processing_time_ms=int(processing_time)
        )
        
        # Update session
        session["messages"].append({"role": "user", "content": user_input})
        session["messages"].append({"role": "assistant", "content": final_state["answer"]})
        session["student_type"] = final_state.get("student_type") or session.get("student_type")
        session["student_level"] = final_state.get("student_level") or session.get("student_level")
        session["detected_programs"] = final_state.get("detected_programs", [])
        session["detected_location"] = final_state.get("detected_location") or session.get("detected_location")
        session["lead_captured"] = final_state.get("lead_captured", False)
        # Progressive lead capture fields
        session["user_name"] = final_state.get("user_name") or session.get("user_name")
        session["name_asked"] = final_state.get("name_asked", session.get("name_asked", False))
        session["lead_capture_completeness"] = final_state.get("lead_capture_completeness", 0)
        
        # Update conversation profile
        self.conversation_manager.update_conversation_profile(
            conversation_id=session["conversation_id"],
            student_type=session["student_type"],
            student_level=session["student_level"],
            detected_location=session["detected_location"],
            programs_discussed=session["detected_programs"]
        )
        
        # Return response
        return {
            "session_id": session_id,
            "answer": final_state["answer"],
            "sources": final_state.get("sources", []),
            "student_type": session["student_type"],
            "student_level": session["student_level"],
            "detected_programs": session["detected_programs"],
            "processing_time_ms": int(processing_time)
        }
    
    def end_conversation(self, session_id: str) -> Dict:
        """
        End a conversation session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation summary for feedback collection
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        conversation_id = session["conversation_id"]
        
        # Calculate conversation duration
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                created_at,
                total_messages,
                student_type,
                student_level,
                programs_discussed
            FROM conversations
            WHERE id = %s
        """, (conversation_id,))
        
        conv = cursor.fetchone()
        
        if conv:
            duration_seconds = int((datetime.now() - conv['created_at']).total_seconds())
            
            # Update conversation end time
            cursor.execute("""
                UPDATE conversations
                SET ended_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (conversation_id,))
            self.conn.commit()
            
            return {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "total_messages": conv['total_messages'],
                "duration_seconds": duration_seconds,
                "student_type": conv['student_type'],
                "student_level": conv['student_level'],
                "programs_discussed": conv['programs_discussed'] or []
            }
        
        return {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "total_messages": len(session["messages"]) // 2,
            "duration_seconds": 0
        }
    
    def submit_feedback(
        self,
        session_id: str,
        rating: str,
        suggestion: Optional[str] = None,
        user_ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Submit feedback for a conversation
        
        Args:
            session_id: Session identifier
            rating: Feedback rating ('bad', 'average', 'good')
            suggestion: Optional textual suggestion
            user_ip_address: User's IP address
            user_agent: User's browser/device info
            
        Returns:
            Feedback ID
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        conversation_id = session["conversation_id"]
        
        # Get conversation details
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT created_at, total_messages
            FROM conversations
            WHERE id = %s
        """, (conversation_id,))
        
        conv = cursor.fetchone()
        
        total_messages = conv['total_messages'] if conv else len(session["messages"]) // 2
        duration_seconds = int((datetime.now() - conv['created_at']).total_seconds()) if conv else 0
        
        # Submit feedback
        feedback_id = self.feedback_manager.submit_feedback(
            conversation_id=conversation_id,
            session_id=session_id,
            rating=rating,
            suggestion=suggestion,
            total_messages=total_messages,
            conversation_duration_seconds=duration_seconds,
            user_ip_address=user_ip_address,
            user_agent=user_agent
        )
        
        return feedback_id
    
    def get_session_summary(self, session_id: str) -> Dict:
        """
        Get summary of a conversation session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "conversation_id": session["conversation_id"],
            "total_messages": len(session["messages"]) // 2,
            "student_type": session.get("student_type"),
            "student_level": session.get("student_level"),
            "detected_programs": session.get("detected_programs", []),
            "lead_captured": session.get("lead_captured", False)
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    """
    Example usage
    """
    
    print("Conversational RAG System loaded successfully!")
    print("\n✅ 3-Agent Architecture:")
    print("  1. Router Agent (intent, detection, guardrails)")
    print("  2. RAG Agent (enhanced search, answer generation)")
    print("  3. Lead Capture Agent (natural data collection)")
    print("\n✅ Features:")
    print("  • Hybrid search with re-ranking")
    print("  • Comprehensive guardrails")
    print("  • Student type detection")
    print("  • Consultative approach")
    print("  • Conversation memory")
    print("  • Lead capture with email")
    print("  • Feedback collection (bad, average, good)")
    
    # Example usage:
    # system = ConversationalRAGSystem(
    #     db_connection_string="postgresql://...",
    #     openai_api_key=os.getenv("OPENAI_API_KEY"),
    #     anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    # )
    # 
    # # Chat
    # response = system.chat("What are the requirements for MSc AI?")
    # print(response["answer"])
    # session_id = response["session_id"]
    # 
    # # End conversation
    # summary = system.end_conversation(session_id)
    # print(f"Conversation ended: {summary['total_messages']} messages")
    # 
    # # Submit feedback
    # feedback_id = system.submit_feedback(
    #     session_id=session_id,
    #     rating="good",
    #     suggestion="Very helpful responses!"
    # )
    # print(f"Feedback submitted: {feedback_id}")
