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
    
    # Similarity threshold
    SIMILARITY_THRESHOLD = 0.40  # 40% minimum similarity
    
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
    
    def _vector_search(self, query: str) -> List[SearchResult]:
        """Perform vector similarity search"""
        # Generate embedding
        embedding_response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
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
        conversation_history: List[Dict] = None
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
        # Check if we have good results
        if not search_results:
            return self._generate_no_results_response(query, conversation_history)
        
        # Calculate search quality
        avg_score = sum(r.final_score for r in search_results) / len(search_results)
        search_quality_score = avg_score
        
        # Build context from search results
        context = self._build_context(search_results)
        
        # Build system prompt with personality and guardrails
        system_prompt = self._build_system_prompt(student_type, student_level)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(query, context, conversation_history)
        
        # Generate answer with Claude 4 Sonnet (best quality/cost balance)
        # Increased to 500 tokens to prevent mid-sentence truncation
        # System prompt instructs model to keep responses concise
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0.7,  # Natural conversational tone (default is 1.0)
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        answer = response.content[0].text
        
        # Extract unique sources with rich metadata (title, url, category)
        # Deduplicate by URL while preserving order by relevance (final_score)
        seen_urls = set()
        sources = []
        for r in sorted(search_results, key=lambda x: x.final_score, reverse=True):
            if r.source_url not in seen_urls:
                seen_urls.add(r.source_url)
                sources.append({
                    "url": r.source_url,
                    "title": r.source_title or self._generate_title_from_url(r.source_url),
                    "category": r.category or "general"
                })
        
        # Clean up answer - remove any source sections the AI might have added
        import re
        # Remove common source section patterns
        patterns = [
            r'\n\n.*?\*\*Sources:\*\*.*?$',  # **Sources:** section
            r'\n\n.*?Sources:.*?$',  # Sources: section
            r'\n\n.*?Useful links:.*?$',  # Useful links: section
            r'\n\n.*?Learn more:.*?$',  # Learn more: section
            r'\n\n.*?📚.*?Sources.*?$',  # Emoji sources
            r'\n\n.*?🔗.*?http.*?$',  # Link emojis with URLs
            r'\n\n.*?•.*?https://www\.stir\.ac\.uk.*?$',  # Bullet points with URLs
        ]
        
        for pattern in patterns:
            answer = re.sub(pattern, '', answer, flags=re.MULTILINE | re.DOTALL)
        
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

DATE-AWARENESS (Critical for Intakes & Deadlines):
- When user asks about "September intake" or "January intake" WITHOUT specifying a year:
  • If we're BEFORE that month in the current year → assume they mean THIS year ({current_year})
  • If we're PAST that month in the current year → assume they mean NEXT year ({current_year + 1})
  • Example: If today is January 2026 and user asks about "September intake" → answer for September 2026
  • Example: If today is October 2026 and user asks about "September intake" → answer for September 2027
- When context contains data from past years (e.g., 2024, 2025), adapt it to the relevant upcoming intake
- For deadlines: If a deadline has already passed, mention the next available intake instead
- Always clarify the year in your response: "For September 2026 intake..." not just "For September intake..."

RESPONSE STYLE (Critical):
- Be CONCISE: 50-100 words max for simple questions, 150 max for complex ones
- Sound HUMAN: Write like you're texting a friend, not writing an essay
- NEVER repeat or rephrase the user's question back to them
- Jump straight to the answer - no preambles like "Great question!" or "I'd be happy to help!"
- Use contractions (it's, you'll, don't) to sound natural

CORE RULES:
1. Answer using ONLY the provided context - be factual
2. URL HANDLING:
   - By default, DON'T include URLs in your response (system shows them in "Related Pages" section)
   - EXCEPTION: If user explicitly asks for "link", "page", "URL", "website", or "where can I find":
     • Include up to 2 most relevant links INLINE using markdown format: [Page Title](url)
     • Example: "Here's the [MSc AI course page](https://www.stir.ac.uk/courses/pg/artificial-intelligence/) with all the details."
     • Make the link text descriptive and natural, not just "click here"
3. NEVER assume or guess:
   - Student's background or nationality
   - Whether they're undergraduate or postgraduate
   - Their student type (UK, international, Scottish)
   - Any personal details not explicitly stated
   Always ASK if you don't know - don't make educated guesses!
4. Stay focused on University of Stirling topics

WHEN YOU NEED MORE INFO:
Ask ONE short question:
- "Which program are you interested in?" or "What course are you looking at?"
- "Are you a UK or international student?"
- "Undergrad or postgrad?"

FEES:
- Quote EXACT figures from context with £ symbol
- If fee not in context: "I don't have that exact fee - our admissions team can help: admissions@stir.ac.uk"

FORMATTING:
- Use **bold** sparingly for key info (fees, deadlines)
- Short bullet points for lists (3-4 max)
- No long numbered lists unless truly needed
- One short follow-up question at the end if relevant

FAREWELLS:
When user says bye/thanks/cheers:
"Good luck with your application! Reach out anytime - admissions@stir.ac.uk or +44 1786 467044. Take care!"

ESCALATION (Use sparingly - only after trying to help first):
1. FIRST: Try to answer with available context
2. IF VAGUE: Ask ONE clarifying question (which program? UK or international? undergrad or postgrad?)
3. AFTER providing useful info: Ask if they need more details or want to speak with admissions
4. ONLY escalate when you genuinely can't help after 2-3 exchanges:
   "I don't have that specific info. Want me to connect you with our admissions team? Just share your name and email."

NEVER escalate on the first message - always try to help or ask clarifying questions first!

BAD EXAMPLES (Don't do this):
❌ "You asked about the fees for MSc AI. The fees for the MSc Artificial Intelligence program are..."
❌ "Great question! I'd be happy to help you with information about..."
❌ "Based on the information provided, I can tell you that..."

GOOD EXAMPLES (Do this):
✓ "MSc AI fees are £24,300/year for international students, £10,500 for UK."
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
        conversation_history: List[Dict] = None
    ) -> str:
        """Build user prompt with query and context"""
        
        prompt_parts = []
        
        # Add conversation history if available (last 6 messages for better context)
        if conversation_history and len(conversation_history) > 0:
            prompt_parts.append("=== CONVERSATION HISTORY ===")
            prompt_parts.append("(Use this to understand context and maintain conversation flow)")
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
        prompt_parts.append("Answer the question using the context above. Maintain conversation flow if there's history.")
        
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
    
    def _generate_no_results_response(self, query: str, conversation_history: List[Dict] = None) -> RAGResponse:
        """Generate response when no good results found - ask clarifying questions first"""
        
        # Count conversation turns to determine if we should escalate or ask questions
        turn_count = len(conversation_history) // 2 if conversation_history else 0
        
        # For first few messages (turns 0-2), ask clarifying questions instead of escalating
        if turn_count < 3:
            # Detect what type of clarification is needed based on query
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['apply', 'application', 'how to']):
                answer = """To help you with the application process, I need a bit more info:

- **Which program** are you interested in? (e.g., MSc Data Science, BA Business)
- Are you looking at **undergraduate or postgraduate** study?

Once I know this, I can give you specific application steps and deadlines!"""
            
            elif any(word in query_lower for word in ['fee', 'cost', 'tuition', 'price']):
                answer = """Fees vary by program and student type. To give you accurate info:

- **Which course** are you interested in?
- Are you a **UK or international** student?

Let me know and I'll get you the exact figures!"""
            
            elif any(word in query_lower for word in ['requirement', 'entry', 'qualification']):
                answer = """Entry requirements depend on the specific program. Could you tell me:

- **Which course** are you considering?
- **Undergrad or postgrad**?

I'll then give you the exact requirements!"""
            
            else:
                answer = """I'd love to help! Could you tell me a bit more about what you're looking for?

For example:
- Which **program or subject area** interests you?
- Are you looking at **undergraduate or postgraduate** study?

This will help me give you the most relevant information!"""
            
            return RAGResponse(
                answer=answer,
                sources=[],
                search_results=[],
                search_quality_score=0.0,
                needs_clarification=True,
                clarification_context="vague_query"
            )
        
        # After 3+ turns of conversation, if still no results, offer escalation
        answer = """I don't have that specific information in my knowledge base. I'd be happy to connect you with our admissions team who can provide a detailed response.

Could you please share:
- Your full name
- Your email address

Our team will review your query and get back to you within 1-2 business days."""
        
        return RAGResponse(
            answer=answer,
            sources=[],
            search_results=[],
            search_quality_score=0.0,
            needs_clarification=True,
            clarification_context=query
        )


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
        
        # 3. Generate answer
        response = self.answer_generator.generate(
            query=query,
            search_results=reranked_results,
            student_type=student_type,
            student_level=student_level,
            conversation_history=conversation_history
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
