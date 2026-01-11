"""
============================================
ENHANCED RAG SYSTEM
============================================
Purpose: Advanced RAG with hybrid search, query expansion, and re-ranking
Features:
- Hybrid search (vector + keyword)
- Query expansion with synonyms
- Re-ranking algorithm
- Similarity threshold filtering
- Conversation memory integration

Version: 2.0
Created: 2025-11-20
============================================
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
import anthropic


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class SearchResult:
    """Individual search result with rich metadata"""
    chunk_id: int
    document_id: int
    content: str
    heading_context: str
    source_url: str
    source_title: str
    category: str
    similarity_score: float
    keyword_score: float = 0.0
    final_score: float = 0.0
    rank: int = 0


@dataclass
class RAGResponse:
    """Complete RAG response"""
    answer: str
    sources: List[str]
    search_results: List[SearchResult]
    search_quality_score: float
    needs_clarification: bool = False
    clarification_context: Optional[str] = None


# ============================================
# CONFIGURATION
# ============================================

class RAGConfig:
    """Configuration for enhanced RAG"""
    
    # Search parameters
    TOP_K_VECTOR = 10  # Retrieve more for re-ranking
    TOP_K_KEYWORD = 5
    TOP_K_FINAL = 3    # Final results after re-ranking
    
    # Source filtering
    MAX_SOURCES = 2    # Maximum sources to show in response
    MIN_SOURCE_SCORE = 0.50  # Minimum score for a source to be included
    
    # Similarity threshold
    SIMILARITY_THRESHOLD = 0.30  # 30% minimum similarity (lowered to retrieve more candidates)
    LOW_QUALITY_THRESHOLD = 0.45  # If avg score below this, ask clarifying questions
    
    # Re-ranking weights
    WEIGHT_VECTOR_SIMILARITY = 0.5
    WEIGHT_KEYWORD_MATCH = 0.2
    WEIGHT_EXACT_PROGRAM_MATCH = 0.15
    WEIGHT_RECENCY = 0.10
    WEIGHT_CATEGORY_PRIORITY = 0.05
    
    # Category priorities (higher = more relevant)
    CATEGORY_PRIORITIES = {
        'courses': 1.0,
        'admissions': 0.9,
        'fees_funding': 0.9,
        'international': 0.8,
        'campus_life': 0.7,
        'about': 0.5,
    }
    
    # Query expansion
    SYNONYM_MAP = {
        'requirements': ['criteria', 'qualifications', 'prerequisites'],
        'fees': ['tuition', 'cost', 'price', 'charges'],
        'scholarships': ['funding', 'bursaries', 'financial aid'],
        'apply': ['application', 'admission', 'enroll'],
        'program': ['course', 'degree', 'programme'],
        'international': ['overseas', 'foreign'],
        'undergraduate': ['UG', 'bachelors', 'BSc', 'BA'],
        'postgraduate': ['PG', 'masters', 'MSc', 'MA', 'PhD'],
    }
    
    # Program code mappings (for query expansion)
    PROGRAM_CODES = {
        'computer science': 'G400',
        'artificial intelligence': 'G7P9',
        'data science': 'G300',
        'business management': 'N200',
        'psychology': 'C800',
    }


# ============================================
# QUERY EXPANSION
# ============================================

class QueryExpander:
    """Expands queries with synonyms and program codes"""
    
    @staticmethod
    def expand(query: str, student_level: Optional[str] = None) -> str:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original query
            student_level: Student level for context
            
        Returns:
            Expanded query string
        """
        expanded_terms = [query]
        query_lower = query.lower()
        
        # Add synonyms
        for term, synonyms in RAGConfig.SYNONYM_MAP.items():
            if term in query_lower:
                expanded_terms.extend(synonyms)
        
        # Add program codes if program mentioned
        for program, code in RAGConfig.PROGRAM_CODES.items():
            if program in query_lower:
                expanded_terms.append(code)
        
        # Add level-specific terms
        if student_level:
            if student_level == 'undergraduate':
                expanded_terms.extend(['UG', 'bachelors'])
            elif student_level == 'postgraduate':
                expanded_terms.extend(['PG', 'masters', 'taught'])
            elif student_level == 'phd':
                expanded_terms.extend(['research', 'doctorate'])
        
        # Join and deduplicate
        expanded = ' '.join(set(expanded_terms))
        return expanded


# ============================================
# HYBRID SEARCH
# ============================================

class HybridSearch:
    """Combines vector and keyword search"""
    
    def __init__(self, db_connection, openai_client: OpenAI):
        """
        Initialize hybrid search
        
        Args:
            db_connection: PostgreSQL connection
            openai_client: OpenAI client for embeddings
        """
        self.conn = db_connection
        self.openai_client = openai_client
    
    def search(
        self,
        query: str,
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        conversation_context: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector and keyword
        
        Args:
            query: Search query
            student_type: Type of student (for personalization)
            student_level: Level of study
            conversation_context: Previous conversation context
            
        Returns:
            List of SearchResult objects
        """
        # 1. Expand query
        expanded_query = QueryExpander.expand(query, student_level)
        
        # 2. Vector search
        vector_results = self._vector_search(expanded_query)
        
        # 3. Keyword search
        keyword_results = self._keyword_search(expanded_query)
        
        # 4. Merge and deduplicate
        merged_results = self._merge_results(vector_results, keyword_results)
        
        # 5. Filter by similarity threshold
        filtered_results = [
            r for r in merged_results 
            if r.similarity_score >= RAGConfig.SIMILARITY_THRESHOLD
        ]
        
        return filtered_results
    
    def _get_embedding(self, query: str) -> List[float]:
        """Generate embedding for query"""
        embedding_response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        return embedding_response.data[0].embedding
    
    def _vector_search(self, query: str) -> List[SearchResult]:
        """Perform vector similarity search"""
        # Get embedding for query
        query_embedding = self._get_embedding(query)
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Vector search with pgvector
        cursor.execute("""
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.content,
                c.heading_context,
                d.url as source_url,
                d.title as source_title,
                d.category,
                1 - (c.embedding <=> %s::vector) as similarity_score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, RAGConfig.TOP_K_VECTOR))
        
        results = []
        for row in cursor.fetchall():
            results.append(SearchResult(
                chunk_id=row['chunk_id'],
                document_id=row['document_id'],
                content=row['content'],
                heading_context=row['heading_context'] or '',
                source_url=row['source_url'],
                source_title=row['source_title'] or '',
                category=row['category'],
                similarity_score=float(row['similarity_score'])
            ))
        
        return results
    
    def _keyword_search(self, query: str) -> List[SearchResult]:
        """Perform keyword-based full-text search"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # PostgreSQL full-text search
        cursor.execute("""
            SELECT 
                c.id as chunk_id,
                c.document_id,
                c.content,
                c.heading_context,
                d.url as source_url,
                d.title as source_title,
                d.category,
                ts_rank(
                    to_tsvector('english', c.content || ' ' || COALESCE(c.heading_context, '')),
                    plainto_tsquery('english', %s)
                ) as keyword_score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE to_tsvector('english', c.content || ' ' || COALESCE(c.heading_context, '')) 
                @@ plainto_tsquery('english', %s)
            ORDER BY keyword_score DESC
            LIMIT %s
        """, (query, query, RAGConfig.TOP_K_KEYWORD))
        
        results = []
        for row in cursor.fetchall():
            results.append(SearchResult(
                chunk_id=row['chunk_id'],
                document_id=row['document_id'],
                content=row['content'],
                heading_context=row['heading_context'] or '',
                source_url=row['source_url'],
                source_title=row['source_title'] or '',
                category=row['category'],
                similarity_score=0.0,  # No vector score for keyword results
                keyword_score=float(row['keyword_score'])
            ))
        
        return results
    
    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Merge and deduplicate results from both searches"""
        # Create dictionary keyed by chunk_id
        merged = {}
        
        # Add vector results
        for result in vector_results:
            merged[result.chunk_id] = result
        
        # Add/merge keyword results
        for result in keyword_results:
            if result.chunk_id in merged:
                # Update keyword score
                merged[result.chunk_id].keyword_score = result.keyword_score
            else:
                # Add new result
                merged[result.chunk_id] = result
        
        return list(merged.values())


# ============================================
# RE-RANKING
# ============================================

class ReRanker:
    """Re-ranks search results based on multiple factors"""
    
    @staticmethod
    def rerank(
        results: List[SearchResult],
        query: str,
        student_type: Optional[str] = None,
        detected_programs: List[str] = None
    ) -> List[SearchResult]:
        """
        Re-rank results based on multiple factors
        
        Args:
            results: Initial search results
            query: Original query
            student_type: Type of student
            detected_programs: Programs mentioned in conversation
            
        Returns:
            Re-ranked list of SearchResult objects
        """
        query_lower = query.lower()
        detected_programs = detected_programs or []
        
        for result in results:
            content_lower = result.content.lower()
            heading_lower = result.heading_context.lower()
            
            # Calculate component scores
            vector_score = result.similarity_score
            keyword_score = result.keyword_score
            
            # Exact program match bonus
            program_match_score = 0.0
            for program in detected_programs:
                if program.lower() in content_lower or program.lower() in heading_lower:
                    program_match_score = 1.0
                    break
            
            # Category priority
            category_score = RAGConfig.CATEGORY_PRIORITIES.get(
                result.category, 0.5
            )
            
            # Recency score (placeholder - would need document dates)
            recency_score = 0.5
            
            # Calculate final weighted score
            final_score = (
                RAGConfig.WEIGHT_VECTOR_SIMILARITY * vector_score +
                RAGConfig.WEIGHT_KEYWORD_MATCH * keyword_score +
                RAGConfig.WEIGHT_EXACT_PROGRAM_MATCH * program_match_score +
                RAGConfig.WEIGHT_CATEGORY_PRIORITY * category_score +
                RAGConfig.WEIGHT_RECENCY * recency_score
            )
            
            result.final_score = final_score
        
        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results, 1):
            result.rank = i
        
        # Return top K
        return results[:RAGConfig.TOP_K_FINAL]


# ============================================
# ANSWER GENERATION
# ============================================

class AnswerGenerator:
    """Generates answers using Claude with retrieved context"""
    
    def __init__(self, anthropic_client: anthropic.Anthropic):
        """
        Initialize answer generator
        
        Args:
            anthropic_client: Anthropic client for Claude
        """
        self.client = anthropic_client
    
    def generate(
        self,
        query: str,
        search_results: List[SearchResult],
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        conversation_history: List[Dict] = None,
        detected_programs: List[str] = None
    ) -> RAGResponse:
        """
        Generate answer using Claude
        
        Args:
            query: User's question
            search_results: Retrieved and re-ranked results
            student_type: Type of student
            student_level: Level of study
            conversation_history: Previous messages
            
        Returns:
            RAGResponse with answer and metadata
        """
        detected_programs = detected_programs or []
        
        # Check if we have good results
        if not search_results:
            return self._generate_no_results_response(query, conversation_history, student_type, student_level, detected_programs)
        
        # Calculate search quality
        avg_score = sum(r.final_score for r in search_results) / len(search_results)
        search_quality_score = avg_score
        
        # Check if we have conversation context that can help with low-quality results
        has_useful_context = (
            bool(detected_programs) or 
            (student_type and student_type != 'unknown') or
            (student_level and student_level != 'unknown')
        )
        
        # If search quality is low AND we have no context, ask clarifying questions
        # But if we have context, let the LLM use it intelligently
        if avg_score < RAGConfig.LOW_QUALITY_THRESHOLD and not has_useful_context:
            return self._generate_clarification_response(query, search_results, conversation_history, student_type, student_level, detected_programs)
        
        # Build context from search results
        context = self._build_context(search_results)
        
        # Build system prompt with personality and guardrails
        system_prompt = self._build_system_prompt(student_type, student_level)
        
        # Build user prompt with conversation state for context-aware responses
        user_prompt = self._build_user_prompt(
            query, context, conversation_history,
            student_type, student_level, detected_programs
        )
        
        # Generate answer with Claude Sonnet 4 (reliable, working model)
        # Good instruction following and consistent output
        # Response time ~8-12 seconds
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0.7,  # Natural conversational tone (default is 1.0)
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        answer = response.content[0].text
        
        # Extract unique sources with rich metadata (title, url, category)
        # Only include sources that meet minimum relevance score
        # Limit to MAX_SOURCES to keep links relevant
        seen_urls = set()
        sources = []
        for r in sorted(search_results, key=lambda x: x.final_score, reverse=True):
            if r.source_url not in seen_urls and r.final_score >= RAGConfig.MIN_SOURCE_SCORE:
                seen_urls.add(r.source_url)
                sources.append({
                    "url": r.source_url,
                    "title": r.source_title or self._generate_title_from_url(r.source_url),
                    "category": r.category or "general",
                    "relevance_score": round(r.final_score, 3)
                })
                # Limit to configured max sources
                if len(sources) >= RAGConfig.MAX_SOURCES:
                    break
        
        # Clean up answer - remove any source sections the AI might have added
        import re
        # Remove specific source sections - more precise patterns
        patterns = [
            r'\n\*\*Sources:\*\*.*$',  # **Sources:** section (more precise)
            r'\nSources:.*$',  # Sources: section (more precise)
            r'\nUseful links:.*$',  # Useful links: section (more precise)
            r'\nLearn more:.*$',  # Learn more: section (more precise)
        ]
        
        for pattern in patterns:
            answer = re.sub(pattern, '', answer, flags=re.MULTILINE)
        
        # Remove any remaining URLs at the end
        answer = re.sub(r'\n\nhttps://.*?$', '', answer, flags=re.MULTILINE)
        answer = answer.strip()
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            search_results=search_results,
            search_quality_score=search_quality_score,
            needs_clarification=False
        )
    
    def _build_context(self, results: List[SearchResult]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}]")
            if result.heading_context:
                context_parts.append(f"Section: {result.heading_context}")
            context_parts.append(result.content)
            context_parts.append(f"URL: {result.source_url}")
            context_parts.append("")  # Blank line
        
        return "\n".join(context_parts)
    
    def _build_system_prompt(
        self,
        student_type: Optional[str],
        student_level: Optional[str]
    ) -> str:
        """Build system prompt with personality and guidelines"""
        from datetime import datetime
        
        current_date = datetime.now()
        current_month = current_date.strftime("%B")
        current_year = current_date.year
        
        base_prompt = f"""You are a friendly admissions assistant for the University of Stirling. Chat naturally like a helpful human advisor.

TODAY'S DATE: {current_date.strftime("%d %B %Y")} (Current month: {current_month}, Current year: {current_year})

═══════════════════════════════════════════════════════════════
DECISION LOGIC - FOLLOW THIS EXACT ORDER (CRITICAL)
═══════════════════════════════════════════════════════════════

STEP 1: Does the context contain information that DIRECTLY answers the user's question?
  → YES: Answer using that information. Be specific and helpful.
  → NO: Go to Step 2.

STEP 2: Does the context contain RELATED but not exact information?
  → YES: Share what you DO have, then ask ONE clarifying question to get closer.
         Example: "I have info on MSc programs in this area. Are you looking at undergraduate or postgraduate?"
  → NO: Go to Step 3.

STEP 3: Is the user asking about a topic where you need more details to help?
  → YES: Ask ONE specific clarifying question (program name, UK/international, undergrad/postgrad)
  → NO: Offer to connect with admissions team.

GOLDEN RULE: If context has ANY relevant information, USE IT. Never say "I don't have information" when the context contains related content. Extract value from what you have.

═══════════════════════════════════════════════════════════════
TOPIC SWITCHING - CRITICAL
═══════════════════════════════════════════════════════════════

When user switches to a NEW topic (e.g., from AI to Economics):
- IGNORE previous conversation topics completely
- Focus ONLY on the new topic they're asking about
- The context provided is already filtered for their NEW question
- Never say "I see you're now interested in X instead of Y" - just answer about X
- Never reference what you discussed before unless user explicitly asks

BAD: "I can see you're interested in Economics now. Unfortunately, I don't have specific information about PhD programs in Economics - the context I have covers AI programs."
GOOD: "For PhD Economics at Stirling, you'll need [answer from context]..."

═══════════════════════════════════════════════════════════════
CORE RULES
═══════════════════════════════════════════════════════════════

1. Answer using ONLY the provided context - be factual
2. Stay focused on University of Stirling topics
3. NEVER assume or guess:
   - Student's background or nationality
   - Whether they're undergraduate or postgraduate
   - Their student type (UK, international, Scottish)
   - Any personal details not explicitly stated
   Always ASK if you don't know - don't make educated guesses!

═══════════════════════════════════════════════════════════════
RESPONSE STYLE
═══════════════════════════════════════════════════════════════

- Be CONCISE: 50-100 words for simple questions, 150 max for complex
- Sound HUMAN: Write like texting a friend, use contractions (it's, you'll, don't)
- Jump straight to the answer - no preambles like "Great question!" or "I'd be happy to help!"
- NEVER repeat the user's question back to them
- ALWAYS FRAME POSITIVELY:
  • Lead with what you CAN help with
  • Never start with "Unfortunately", "I'm sorry but", "I don't have"
  • Instead of "I don't have X" → "Here's what I can tell you about [topic]..."

═══════════════════════════════════════════════════════════════
DATE-AWARENESS (Intakes & Deadlines)
═══════════════════════════════════════════════════════════════

- "September intake" without year: If before September → this year ({current_year}), if after → next year ({current_year + 1})
- "January intake" without year: If before January → this year ({current_year}), if after → next year ({current_year + 1})
- Adapt past year data (2024, 2025) to upcoming intakes
- For deadlines: If already passed, mention the next available intake
- Always clarify year: "For September {current_year} intake..." not just "For September intake..."

═══════════════════════════════════════════════════════════════
APPLICATION LINKS (Use these EXACT URLs - ignore any others from context)
═══════════════════════════════════════════════════════════════

- Postgraduate Taught (Masters): https://portal.stir.ac.uk/student/course-application/pg/application.jsp
- Postgraduate Research (PhD/MPhil): https://portal.stir.ac.uk/student/course-application/pgr/application.jsp
- Undergraduate: https://portal.stir.ac.uk/student/course-application/ugd/application.jsp

When user wants to apply or asks for application link:
- PhD/MPhil/Doctoral/Research degree → use Postgraduate Research link
- Masters/MSc/MA/MBA/MLitt/postgraduate taught → use Postgraduate Taught link
- Undergraduate/bachelors/BA/BSc → use Undergraduate link
- If unclear, ASK: "Are you applying for undergraduate, a taught Masters, or a research degree (PhD/MPhil)?"

═══════════════════════════════════════════════════════════════
URL FORMATTING (CRITICAL)
═══════════════════════════════════════════════════════════════

- Use SINGLE bracket markdown: [Link Text](url)
- CORRECT: [MSc Artificial Intelligence](https://www.stir.ac.uk/courses/pg/artificial-intelligence/)
- CORRECT: [BSc Biology](https://www.stir.ac.uk/courses/ug/biology)
- WRONG: [[MSc AI](url) ← NO double brackets!
- WRONG: MSc AI](url) ← Missing opening [
- WRONG: [MSc AI - description ← NO standalone [ without closing ]
- NEVER use double brackets [[ - always single [
- NEVER start a line with [ unless it's a complete markdown link [text](url)
- NEVER use [ for bullet points or list items - use • or - instead
- Include up to 2 relevant links per response
- Make link text the program name or page title, not "click here"
- Use URLs from context's source URLs for program pages

═══════════════════════════════════════════════════════════════
FEES
═══════════════════════════════════════════════════════════════

- Quote EXACT figures with £ symbol from context
- If not in context: "For the most accurate fee information, our admissions team can help: admissions@stir.ac.uk"

═══════════════════════════════════════════════════════════════
FORMATTING
═══════════════════════════════════════════════════════════════

- **Bold** for key info (fees, deadlines)
- Short bullet points (3-4 max)
- No long numbered lists unless truly needed
- One follow-up question at end if relevant

═══════════════════════════════════════════════════════════════
CLARIFYING QUESTIONS (When you need more info)
═══════════════════════════════════════════════════════════════

Ask ONE short question:
- "Which program are you interested in?" or "What course are you looking at?"
- "Are you a UK or international student?"
- "Undergrad or postgrad?"

═══════════════════════════════════════════════════════════════
ESCALATION (Use sparingly - only after trying to help first)
═══════════════════════════════════════════════════════════════

1. FIRST: Try to answer with available context
2. IF VAGUE: Ask ONE clarifying question
3. AFTER providing useful info: Ask if they need more details
4. ONLY escalate when you genuinely can't help after 2-3 exchanges:
   "Want me to connect you with our admissions team? Just share your name and email."

NEVER escalate on the first message - always try to help or ask clarifying questions first!

═══════════════════════════════════════════════════════════════
CONTACT DETAILS FORMATTING
═══════════════════════════════════════════════════════════════

When mentioning contact details, always use these exact formats (UI will auto-link them):
- Email: admissions@stir.ac.uk (plain text, no markdown)
- Phone: +44 1786 467044 (with +44 prefix and spaces)
- Never wrap emails or phone numbers in markdown links - just write them as plain text

═══════════════════════════════════════════════════════════════
FAREWELLS
═══════════════════════════════════════════════════════════════

When user says bye/thanks/cheers:
"Good luck with your application! Reach out anytime - admissions@stir.ac.uk or +44 1786 467044. Take care!"

═══════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════

BAD:
❌ "I can see you're interested in Economics now. Unfortunately, I don't have specific information..."
❌ "You asked about the fees for MSc AI. The fees are..."
❌ "Great question! I'd be happy to help..."
❌ "Based on the information provided, I can tell you that..."

GOOD:
✓ "MSc AI fees are £24,300/year for international students, £10,500 for UK."
✓ "PhD Economics at Stirling focuses on [info from context]. Entry requirements include..."
✓ "The deadline is January 15th. Need help with your application?"
✓ "Entry requirements: 2:1 degree in a related field + IELTS 6.0. Which part would you like more detail on?\""""
        
        # Add student-specific context if known
        if student_type and student_type != 'unknown':
            if student_type == 'scottish':
                base_prompt += "\n\nNote: This student may be eligible for SAAS funding (mention after confirming domicile)."
            elif student_type == 'uk':
                base_prompt += "\n\nNote: This UK student may be eligible for Student Finance (mention when discussing fees)."
            elif student_type == 'international':
                base_prompt += "\n\nNote: This international student will need visa and English language info (include when relevant)."
        
        return base_prompt
    
    def _build_user_prompt(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict] = None,
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        detected_programs: List[str] = None
    ) -> str:
        """Build user prompt with query, context, and conversation state"""
        
        prompt_parts = []
        detected_programs = detected_programs or []
        
        # Add what we already know about this user (CRITICAL for context-aware responses)
        known_facts = []
        if detected_programs:
            known_facts.append(f"Program interest: {', '.join(detected_programs)}")
        if student_type and student_type != 'unknown':
            known_facts.append(f"Student type: {student_type}")
        if student_level and student_level != 'unknown':
            known_facts.append(f"Study level: {student_level}")
        
        if known_facts:
            prompt_parts.append("=== WHAT WE KNOW ABOUT THIS USER (USE THIS!) ===")
            for fact in known_facts:
                prompt_parts.append(f"• {fact}")
            prompt_parts.append("")
            prompt_parts.append("IMPORTANT: Use this information when answering. Do NOT ask for info we already have.")
            prompt_parts.append("If user says something vague like 'I am international student', combine it with known program interest.")
            prompt_parts.append("=== END USER PROFILE ===")
            prompt_parts.append("")
        
        # Add conversation history if available (last 6 messages for better context)
        if conversation_history and len(conversation_history) > 0:
            prompt_parts.append("=== CONVERSATION HISTORY (Reference Only) ===")
            prompt_parts.append("")
            # Include last 6 messages (3 exchanges) for full context
            for msg in conversation_history[-6:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")
            prompt_parts.append("=== END CONVERSATION HISTORY ===")
            prompt_parts.append("")
        
        # Add context
        prompt_parts.append("=== RELEVANT INFORMATION FROM STIRLING UNIVERSITY ===")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("=== END INFORMATION ===")
        prompt_parts.append("")
        
        # Add current query
        prompt_parts.append("=== CURRENT QUESTION ===")
        prompt_parts.append(f"{query}")
        prompt_parts.append("")
        
        # Build smart instructions based on what we know
        if known_facts:
            prompt_parts.append("""INSTRUCTIONS:
1. The user profile above shows what we already know - USE IT
2. Combine the current question with known context (e.g., if we know they're interested in MSc AI and they say "I'm international", answer about MSc AI for international students)
3. Only ask for info that's MISSING from the user profile
4. If context doesn't have specific info for their situation, say what you DO have and ask ONE clarifying question""")
        else:
            prompt_parts.append("""INSTRUCTIONS:
1. Answer using the context above
2. If the question is vague and you need more info, ask ONE specific clarifying question
3. Focus on being helpful - share what you CAN tell them""")
        
        return "\n".join(prompt_parts)
    
    def _generate_title_from_url(self, url: str) -> str:
        """Generate a human-readable title from URL path"""
        # Remove base URL and get path segments
        path = url.replace('https://www.stir.ac.uk/', '').replace('https://stir.ac.uk/', '')
        segments = [s for s in path.split('/') if s]
        
        if not segments:
            return "University of Stirling"
        
        # Common path mappings for better titles
        title_mappings = {
            'courses': 'Courses',
            'pg': 'Postgraduate',
            'ug': 'Undergraduate',
            'fees': 'Tuition Fees',
            'scholarships': 'Scholarships',
            'accommodation': 'Accommodation',
            'admissions': 'Admissions',
            'international': 'International Students',
            'about': 'About Stirling',
            'research': 'Research',
            'student-life': 'Student Life',
            'campus': 'Campus',
        }
        
        # Build title from path segments
        title_parts = []
        for segment in segments[-2:]:  # Use last 2 segments for concise title
            # Check if we have a mapping
            if segment.lower() in title_mappings:
                title_parts.append(title_mappings[segment.lower()])
            else:
                # Convert slug to title case
                title_parts.append(segment.replace('-', ' ').replace('_', ' ').title())
        
        return ' - '.join(title_parts) if title_parts else "University of Stirling"
    
    def _generate_no_results_response(
        self,
        query: str,
        conversation_history: List[Dict] = None,
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        detected_programs: List[str] = None
    ) -> RAGResponse:
        """Generate smart response when no results found - uses conversation context"""
        
        detected_programs = detected_programs or []
        
        # Build acknowledgment of what we already know
        known_parts = []
        missing_parts = []
        
        if detected_programs:
            known_parts.append(f"interested in **{detected_programs[-1]}**")
        else:
            missing_parts.append("which **program or subject area** interests you")
        
        if student_type and student_type != 'unknown':
            known_parts.append(f"**{student_type}** student")
        else:
            missing_parts.append("**UK or international** student")
        
        if student_level and student_level != 'unknown':
            known_parts.append(f"**{student_level}** level")
        else:
            missing_parts.append("**undergraduate or postgraduate**")
        
        # Count conversation turns
        turn_count = len(conversation_history) // 2 if conversation_history else 0
        
        # Build context-aware response
        if known_parts and missing_parts:
            # We know some things, ask only for what's missing
            known_str = ", ".join(known_parts)
            answer = f"I see you're {known_str}. To help you better, could you tell me {missing_parts[0]}?"
        elif known_parts and not missing_parts:
            # We know everything but still no results - offer escalation
            known_str = ", ".join(known_parts)
            answer = f"""I see you're {known_str}, but I don't have specific information for this in my knowledge base.

Would you like me to connect you with our admissions team? Just share your name and email, and they'll get back to you within 1-2 business days."""
        elif turn_count < 3:
            # Early in conversation, no context - ask clarifying questions
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['apply', 'application', 'how to']):
                answer = """To help with applications, I need a bit more info:

- **Which program** are you interested in?
- Are you looking at **undergraduate or postgraduate** study?"""
            
            elif any(word in query_lower for word in ['fee', 'cost', 'tuition', 'price']):
                answer = """Fees vary by program and student type. Could you tell me:

- **Which course** are you interested in?
- Are you a **UK or international** student?"""
            
            elif any(word in query_lower for word in ['requirement', 'entry', 'qualification']):
                answer = """Entry requirements depend on the program. Could you tell me:

- **Which course** are you considering?
- **Undergrad or postgrad**?"""
            
            else:
                answer = """I'd love to help! Could you tell me:

- Which **program or subject area** interests you?
- Are you looking at **undergraduate or postgraduate** study?"""
        else:
            # Late in conversation, no context - offer escalation
            answer = """I don't have that specific information. Would you like me to connect you with our admissions team?

Just share your name and email, and they'll get back to you within 1-2 business days."""
        
        return RAGResponse(
            answer=answer,
            sources=[],
            search_results=[],
            search_quality_score=0.0,
            needs_clarification=True,
            clarification_context="no_results"
        )
    
    def _generate_clarification_response(
        self,
        query: str,
        search_results: List[SearchResult],
        conversation_history: List[Dict] = None,
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        detected_programs: List[str] = None
    ) -> RAGResponse:
        """
        Generate SMART clarifying questions when search results are low quality.
        Acknowledges what we already know and only asks for missing info.
        """
        detected_programs = detected_programs or []
        query_lower = query.lower()
        
        # Build what we know vs what's missing
        known_parts = []
        missing_parts = []
        
        if detected_programs:
            known_parts.append(f"interested in **{detected_programs[-1]}**")
        else:
            missing_parts.append("program")
        
        if student_type and student_type != 'unknown':
            known_parts.append(f"**{student_type}** student")
        else:
            missing_parts.append("student_type")
        
        if student_level and student_level != 'unknown':
            known_parts.append(f"**{student_level}** level")
        else:
            missing_parts.append("level")
        
        # If we have context, build a smart response acknowledging what we know
        if known_parts:
            known_str = ", ".join(known_parts)
            
            # Determine what single piece of info would help most
            if "program" in missing_parts:
                question = "Which **program or subject area** are you interested in?"
            elif "level" in missing_parts:
                question = "Are you looking at **undergraduate or postgraduate** study?"
            elif "student_type" in missing_parts:
                question = "Are you a **UK or international** student?"
            else:
                question = "What specific aspect would you like to know about? (fees, requirements, deadlines, etc.)"
            
            answer = f"I see you're {known_str}. {question}"
        else:
            # No context - use query-based clarification (existing logic)
            if any(word in query_lower for word in ['fee', 'cost', 'tuition', 'price', 'how much']):
                answer = """Fees vary by program and student type. Could you tell me:

- **Which program** are you interested in?
- Are you a **UK or international** student?"""
            
            elif any(word in query_lower for word in ['requirement', 'entry', 'qualification', 'need', 'eligible']):
                answer = """Entry requirements vary by program. Could you tell me:

- **Which course** are you considering?
- **Undergrad or postgrad**?"""
            
            elif any(word in query_lower for word in ['apply', 'application', 'deadline', 'how to']):
                answer = """To help with applications, could you tell me:

- **Which program** are you applying for?
- **Undergraduate, Masters, or PhD**?"""
            
            elif any(word in query_lower for word in ['scholarship', 'funding', 'bursary', 'financial']):
                answer = """To find the best scholarships for you:

- Are you a **UK or international** student?
- Which **program** are you interested in?"""
            
            else:
                answer = """I'd love to help! Could you tell me:

- Which **program or subject area** interests you?
- Are you looking at **undergraduate or postgraduate** study?"""
        
        return RAGResponse(
            answer=answer,
            sources=[],
            search_results=search_results,
            search_quality_score=sum(r.final_score for r in search_results) / len(search_results) if search_results else 0,
            needs_clarification=True,
            clarification_context="low_quality_results"
        )


# ============================================
# FOLLOW-UP QUESTION GENERATOR
# ============================================

def generate_follow_up_questions(
    query: str,
    answer: str,
    detected_programs: List[str] = None,
    student_type: str = None,
    student_level: str = None
) -> List[Dict]:
    """
    Generate 2 context-aware follow-up questions based on conversation topic.
    Returns list of dicts with 'text' and 'icon' keys.
    """
    query_lower = query.lower()
    answer_lower = answer.lower()
    
    # Comprehensive question bank organized by topic
    question_bank = {
        'fees': [
            {"text": "What scholarships can help reduce my tuition fees?", "icon": "award"},
            {"text": "Can I pay my tuition fees in monthly installments?", "icon": "credit-card"},
            {"text": "Are there any additional costs I should budget for?", "icon": "receipt"},
        ],
        'courses': [
            {"text": "What are the entry requirements for this program?", "icon": "clipboard"},
            {"text": "What career opportunities does this degree lead to?", "icon": "briefcase"},
            {"text": "Is there a part-time study option available?", "icon": "clock"},
        ],
        'requirements': [
            {"text": "What IELTS or English language score do I need?", "icon": "globe"},
            {"text": "Do you consider work experience in place of qualifications?", "icon": "briefcase"},
            {"text": "How do I submit my application and documents?", "icon": "send"},
        ],
        'scholarships': [
            {"text": "When is the deadline to apply for scholarships?", "icon": "calendar"},
            {"text": "Can I combine multiple scholarships together?", "icon": "layers"},
            {"text": "What documents do I need for the scholarship application?", "icon": "file"},
        ],
        'application': [
            {"text": "What documents do I need to complete my application?", "icon": "file"},
            {"text": "How long does the application decision take?", "icon": "clock"},
            {"text": "Can I defer my offer to the next intake?", "icon": "calendar"},
        ],
        'accommodation': [
            {"text": "How much does on-campus accommodation cost per month?", "icon": "home"},
            {"text": "Is accommodation guaranteed for international students?", "icon": "shield"},
            {"text": "What amenities are included in the accommodation?", "icon": "list"},
        ],
        'visa': [
            {"text": "What is the process to apply for a UK student visa?", "icon": "passport"},
            {"text": "Can I work part-time while studying on a student visa?", "icon": "briefcase"},
            {"text": "When should I start my visa application process?", "icon": "calendar"},
        ],
        'intake': [
            {"text": "What is the application deadline for this intake?", "icon": "calendar"},
            {"text": "What are the tuition fees for international students?", "icon": "pound"},
            {"text": "How do I apply for this intake?", "icon": "send"},
        ],
        'campus': [
            {"text": "What sports and recreational facilities are available?", "icon": "activity"},
            {"text": "How do I get from the campus to Stirling city centre?", "icon": "map"},
            {"text": "What student support services are available?", "icon": "heart"},
        ],
        'default': [
            {"text": "What are the tuition fees for this program?", "icon": "pound"},
            {"text": "When is the next application deadline?", "icon": "calendar"},
            {"text": "What scholarships are available for students?", "icon": "award"},
        ]
    }
    
    # Detect primary topic from query
    topic = 'default'
    topic_keywords = {
        'fees': ['fee', 'cost', 'tuition', 'price', 'pay', 'expensive', 'afford'],
        'courses': ['course', 'program', 'degree', 'msc', 'bsc', 'study', 'module', 'curriculum'],
        'requirements': ['requirement', 'qualify', 'eligible', 'need', 'ielts', 'gpa', 'grade'],
        'scholarships': ['scholarship', 'bursary', 'funding', 'financial aid', 'discount'],
        'application': ['apply', 'application', 'submit', 'deadline', 'ucas', 'offer'],
        'accommodation': ['accommodation', 'housing', 'residence', 'dorm', 'room', 'flat'],
        'visa': ['visa', 'immigration', 'cas', 'tier 4', 'sponsor'],
        'intake': ['intake', 'semester', 'start date', 'january', 'september', 'when can i start'],
        'campus': ['campus', 'facility', 'library', 'gym', 'sport', 'location', 'city'],
    }
    
    for topic_name, keywords in topic_keywords.items():
        if any(kw in query_lower for kw in keywords):
            topic = topic_name
            break
    
    # Secondary topic detection from answer if query didn't match
    if topic == 'default':
        for topic_name, keywords in topic_keywords.items():
            if any(kw in answer_lower for kw in keywords):
                topic = topic_name
                break
    
    # Get questions for detected topic
    questions = question_bank.get(topic, question_bank['default']).copy()
    
    # Personalize with detected program name if available
    if detected_programs and len(detected_programs) > 0:
        program = detected_programs[0]
        questions = [
            {
                "text": q["text"].replace("this program", program).replace("this degree", program),
                "icon": q["icon"]
            }
            for q in questions
        ]
    
    return questions[:2]  # Limit to 2 questions for cleaner UI


# ============================================
# MAIN ENHANCED RAG CLASS
# ============================================

class EnhancedRAG:
    """Main class orchestrating the enhanced RAG pipeline"""
    
    def __init__(
        self,
        db_connection,
        openai_api_key: str,
        anthropic_api_key: str
    ):
        """
        Initialize enhanced RAG system
        
        Args:
            db_connection: PostgreSQL connection
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
        """
        self.conn = db_connection
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.hybrid_search = HybridSearch(db_connection, self.openai_client)
        self.answer_generator = AnswerGenerator(self.anthropic_client)
    
    def query(
        self,
        query: str,
        student_type: Optional[str] = None,
        student_level: Optional[str] = None,
        detected_programs: List[str] = None,
        conversation_history: List[Dict] = None,
        conversation_context: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Complete RAG pipeline: search, rerank, generate
        
        Args:
            query: User's question
            student_type: Type of student
            student_level: Level of study
            detected_programs: Programs mentioned
            conversation_history: Previous messages
            conversation_context: Additional context
            
        Returns:
            RAGResponse with answer and metadata
        """
        # 1. Hybrid search
        search_results = self.hybrid_search.search(
            query=query,
            student_type=student_type,
            student_level=student_level,
            conversation_context=conversation_context
        )
        
        # 2. Re-rank results
        reranked_results = ReRanker.rerank(
            results=search_results,
            query=query,
            student_type=student_type,
            detected_programs=detected_programs
        )
        
        # 3. Generate answer with full conversation context
        response = self.answer_generator.generate(
            query=query,
            search_results=reranked_results,
            student_type=student_type,
            student_level=student_level,
            conversation_history=conversation_history,
            detected_programs=detected_programs
        )
        
        return response


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    """
    Example usage of enhanced RAG system
    """
    
    print("Enhanced RAG system loaded successfully!")
    print("\nFeatures:")
    print("✅ Hybrid search (vector + keyword)")
    print("✅ Query expansion with synonyms")
    print("✅ Multi-factor re-ranking")
    print("✅ Similarity threshold filtering")
    print("✅ Conversation memory integration")
    print("✅ Student-type personalization")
    
    # Example usage:
    # conn = psycopg2.connect(...)
    # rag = EnhancedRAG(conn, openai_key, anthropic_key)
    # response = rag.query(
    #     query="What are the requirements for MSc AI?",
    #     student_type="international",
    #     student_level="postgraduate"
    # )
    # print(response.answer)
