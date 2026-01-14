# Part 4: RAG System & AI Components

## 🎯 Learning Objectives

By the end of this section, you will understand:
- What RAG (Retrieval-Augmented Generation) is
- The hybrid search algorithm (vector + keyword)
- How embeddings work
- Claude integration and prompt engineering
- The LangGraph state machine
- Guardrails and safety systems

---

## 4.1 What is RAG?

### The Problem with Pure LLMs

Large Language Models (LLMs) like Claude have limitations:
- **Knowledge cutoff**: Don't know recent information
- **Hallucination**: May make up facts
- **No source attribution**: Can't cite where info came from

### The RAG Solution

RAG = **Retrieval-Augmented Generation**

```
User Question
      │
      ▼
┌─────────────────────────────────────┐
│  1. RETRIEVAL                       │
│     Search database for relevant    │
│     content chunks                  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  2. AUGMENTATION                    │
│     Add retrieved chunks to the     │
│     prompt as context               │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  3. GENERATION                      │
│     LLM generates answer using      │
│     ONLY the provided context       │
└─────────────────────────────────────┘
```

### Benefits

| Benefit | How RAG Achieves It |
|---------|---------------------|
| **Accuracy** | Answers based on real scraped content |
| **Sources** | Can cite exact URLs |
| **Up-to-date** | Just re-scrape to update |
| **Controllable** | LLM only sees approved content |

---

## 4.2 The Enhanced RAG System

**File:** `scripts/enhanced_rag.py`

### Main Classes

```python
# Data classes for structured results
@dataclass
class SearchResult:
    chunk_id: int
    content: str
    source_url: str
    similarity_score: float
    keyword_score: float
    final_score: float

@dataclass
class RAGResponse:
    answer: str
    sources: List[str]
    search_results: List[SearchResult]
    search_quality_score: float

# Main classes
class HybridSearch:      # Combines vector + keyword search
class AnswerGenerator:   # Calls Claude to generate answers
class EnhancedRAG:       # Orchestrates the full pipeline
```

---

## 4.3 Hybrid Search Algorithm

### Why Hybrid?

| Search Type | Good For | Bad For |
|-------------|----------|---------|
| **Vector** | Semantic meaning ("tuition costs" → "fees") | Exact terms (£24,300) |
| **Keyword** | Exact matches, numbers, names | Synonyms, paraphrasing |
| **Hybrid** | Best of both worlds | Slightly more complex |

### The Algorithm

**Location:** `HybridSearch.search()` in `enhanced_rag.py`

```python
def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
    # Step 1: Generate query embedding
    query_embedding = self._get_embedding(query)
    
    # Step 2: Vector search (semantic similarity)
    vector_results = self._vector_search(query_embedding, top_k * 2)
    
    # Step 3: Keyword search (exact matching)
    keyword_results = self._keyword_search(query, top_k * 2)
    
    # Step 4: Combine and re-rank
    combined = self._combine_results(vector_results, keyword_results)
    
    # Step 5: Return top K
    return combined[:top_k]
```

### Vector Search SQL

```sql
SELECT 
    c.id,
    c.content,
    c.heading_context,
    d.url as source_url,
    1 - (c.embedding <-> %s) as similarity_score  -- Cosine similarity
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE c.embedding IS NOT NULL
ORDER BY c.embedding <-> %s  -- Order by distance (closest first)
LIMIT %s
```

### Keyword Search SQL

```sql
SELECT 
    c.id,
    c.content,
    c.heading_context,
    d.url as source_url,
    ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as keyword_score
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
ORDER BY keyword_score DESC
LIMIT %s
```

### Re-Ranking Formula

```python
def _combine_results(self, vector_results, keyword_results):
    # Weights for combining scores
    VECTOR_WEIGHT = 0.7
    KEYWORD_WEIGHT = 0.3
    
    for result in all_results:
        result.final_score = (
            result.similarity_score * VECTOR_WEIGHT +
            result.keyword_score * KEYWORD_WEIGHT
        )
    
    # Sort by final score
    return sorted(all_results, key=lambda x: x.final_score, reverse=True)
```

---

## 4.4 Embeddings

### What Are Embeddings?

Embeddings convert text into numerical vectors that capture meaning.

```
"What are the fees?"     →  [0.023, -0.041, 0.089, ..., 0.012]  (1536 numbers)
"How much does it cost?" →  [0.025, -0.038, 0.091, ..., 0.010]  (similar vector!)
"The weather is nice"    →  [-0.156, 0.234, -0.045, ..., 0.178] (different vector)
```

### OpenAI Embedding API

**Location:** `HybridSearch._get_embedding()` in `enhanced_rag.py`

```python
def _get_embedding(self, text: str) -> List[float]:
    response = self.openai_client.embeddings.create(
        model="text-embedding-3-small",  # 1536 dimensions
        input=text
    )
    return response.data[0].embedding
```

### Embedding Generation Script

**File:** `scripts/generate_embeddings.py`

```python
# Process chunks in batches of 100
for batch in chunks_batches:
    # Get embeddings from OpenAI
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=[chunk.content for chunk in batch]
    )
    
    # Save to database
    for chunk, embedding in zip(batch, response.data):
        cursor.execute(
            "UPDATE chunks SET embedding = %s WHERE id = %s",
            (embedding.embedding, chunk.id)
        )
```

---

## 4.5 Answer Generation with Claude

### The AnswerGenerator Class

**Location:** `AnswerGenerator` in `enhanced_rag.py`

```python
class AnswerGenerator:
    def __init__(self, anthropic_client):
        self.client = anthropic_client
    
    def generate(self, query, search_results, student_type, student_level, conversation_history):
        # Build context from search results
        context = self._build_context(search_results)
        
        # Build prompts
        system_prompt = self._build_system_prompt(student_type, student_level)
        user_prompt = self._build_user_prompt(query, context, conversation_history)
        
        # Call Claude Sonnet 4 (upgraded for superior quality)
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=750,  # Increased for more detailed answers
            temperature=0.7,  # Natural conversational tone
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        return response.content[0].text
```

### System Prompt Structure

```python
def _build_system_prompt(self, student_type, student_level):
    return f"""You are a friendly admissions assistant for the University of Stirling.

TODAY'S DATE: {current_date}

RESPONSE STYLE:
- Be CONCISE: 50-100 words max for simple questions
- Sound HUMAN: Write like texting a friend
- NEVER repeat the user's question back to them
- Jump straight to the answer

CORE RULES:
1. Answer using ONLY the provided context
2. Never include URLs (system adds them automatically)
3. NEVER assume or guess:
   - Student's background or nationality
   - Whether they're undergraduate or postgraduate
   Always ASK if you don't know!
4. Stay focused on University of Stirling topics

WHEN YOU NEED MORE INFO:
Ask ONE short question:
- "Which program are you interested in?"
- "Are you a UK or international student?"
- "Undergrad or postgrad?"

FEES:
- Quote EXACT figures from context with £ symbol
- If not in context: "I don't have that exact fee - admissions@stir.ac.uk"
"""
```

### User Prompt Structure

```python
def _build_user_prompt(self, query, context, conversation_history):
    prompt = ""
    
    # Add conversation history
    if conversation_history:
        prompt += "=== CONVERSATION HISTORY ===\n"
        for msg in conversation_history[-6:]:
            prompt += f"{msg['role'].upper()}: {msg['content']}\n"
    
    # Add retrieved context
    prompt += "=== RELEVANT INFORMATION ===\n"
    prompt += context
    
    # Add current question
    prompt += f"\n=== CURRENT QUESTION ===\n{query}\n"
    prompt += "Answer using the context above."
    
    return prompt
```

---

## 4.6 LangGraph State Machine

### What is LangGraph?

LangGraph is a framework for building stateful, multi-agent AI systems.

**File:** `scripts/conversational_system.py`

### State Definition

```python
class ConversationState(TypedDict):
    # Session identifiers
    session_id: str
    conversation_id: Optional[int]
    
    # Messages
    messages: Annotated[List[BaseMessage], add]
    user_input: str
    conversation_history: List[Dict]
    
    # Intent classification
    intent: Optional[str]
    confidence: float
    
    # Detected information
    student_type: Optional[str]      # scottish, uk, international
    student_level: Optional[str]     # undergraduate, postgraduate
    detected_programs: List[str]
    
    # Output
    answer: Optional[str]
    sources: List[str]
    next_action: str
```

### Graph Creation

```python
def create_conversational_graph(db_connection, openai_key, anthropic_key):
    # Initialize agents
    router_agent = RouterAgent(db_connection, openai_client, guardrail_checker)
    rag_agent = RAGAgent(enhanced_rag)
    lead_capture_agent = LeadCaptureAgent(db_connection)
    
    # Create graph
    workflow = StateGraph(ConversationState)
    
    # Add nodes (agents)
    workflow.add_node("router", router_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("lead_capture", lead_capture_agent)
    
    # Define edges (routing)
    workflow.set_entry_point("router")
    workflow.add_conditional_edges(
        "router",
        route_after_router,  # Function that decides next node
        {
            "rag": "rag",
            "lead_capture": "lead_capture",
            "end": END
        }
    )
    workflow.add_edge("rag", END)
    workflow.add_edge("lead_capture", END)
    
    return workflow.compile()
```

### Routing Logic

```python
def route_after_router(state: ConversationState) -> str:
    next_action = state.get("next_action", "rag")
    
    # If guardrail triggered, end immediately
    if state.get("guardrail_triggered"):
        return "end"
    
    # Route based on intent
    if next_action == "lead_capture":
        return "lead_capture"
    elif next_action == "greeting":
        return "end"  # Greeting handled in router
    else:
        return "rag"
```

---

## 4.7 The Three Agents

### Agent 1: RouterAgent

**Purpose:** Classify intent, run guardrails, detect user info

```python
class RouterAgent:
    def __call__(self, state: ConversationState) -> ConversationState:
        # 1. Run guardrails
        is_valid, response = self.guardrail_checker.check(user_input)
        if not is_valid:
            return {...state, "guardrail_triggered": True, "answer": response}
        
        # 2. Detect student type (UK, international, etc.)
        student_type = self._detect_student_type(user_input)
        
        # 3. Detect student level (undergrad, postgrad)
        student_level = self._detect_student_level(user_input)
        
        # 4. Detect programs mentioned
        programs = self._detect_programs(user_input)
        
        # 5. Classify intent
        intent = self._classify_intent(user_input)
        
        # 6. Decide next action
        if intent == "greeting":
            next_action = "greeting"
        elif ready_for_lead_capture:
            next_action = "lead_capture"
        else:
            next_action = "rag"
        
        return {...state, "intent": intent, "next_action": next_action}
```

### Agent 2: RAGAgent

**Purpose:** Search database, generate answer

```python
class RAGAgent:
    def __call__(self, state: ConversationState) -> ConversationState:
        # Handle greeting
        if state.get("intent") == "greeting":
            return {...state, "answer": self._generate_greeting(state)}
        
        # Build enhanced query with context
        enhanced_query = self._build_enhanced_query(state)
        
        # Query RAG system
        rag_response = self.rag.query(
            query=enhanced_query,
            student_type=state.get("student_type"),
            student_level=state.get("student_level"),
            conversation_history=state.get("conversation_history")
        )
        
        return {...state, "answer": rag_response.answer, "sources": rag_response.sources}
```

### Agent 3: LeadCaptureAgent

**Purpose:** Collect contact information for admissions follow-up

```python
class LeadCaptureAgent:
    def __call__(self, state: ConversationState) -> ConversationState:
        # Extract lead info from message
        lead = self.lead_manager.extract_from_message(user_input)
        
        # If we have email, save lead
        if lead.email:
            self.lead_manager.save_lead_to_db(
                conversation_id=state["conversation_id"],
                lead=lead,
                user_query=user_query,
                conversation_summary=summary
            )
            return {...state, "lead_captured": True, "answer": "Thank you! Our team will contact you..."}
        
        # Otherwise, ask for missing info
        return {...state, "answer": "Could you share your email so we can follow up?"}
```

---

## 4.8 Guardrails System

**File:** `scripts/guardrails.py`

### Purpose

Guardrails protect the chatbot from:
- **Off-topic questions** (not about Stirling)
- **Harassment/abuse**
- **Prompt injection attacks**
- **Sensitive data exposure**

### GuardrailChecker Class

```python
class GuardrailChecker:
    def check(self, user_input, session_id, conversation_id):
        # 1. Check for harassment
        if self._is_harassment(user_input):
            return False, "I'm here to help with university questions..."
        
        # 2. Check for prompt injection
        if self._is_prompt_injection(user_input):
            return False, "I can only help with Stirling University topics."
        
        # 3. Check for off-topic
        if self._is_off_topic(user_input):
            return False, "I specialize in University of Stirling. How can I help with that?"
        
        # 4. Check rate limiting
        if self._is_rate_limited(session_id):
            return False, "Please slow down. Try again in a moment."
        
        return True, None  # All checks passed
```

### Harassment Detection

```python
HARASSMENT_PATTERNS = [
    r'\b(stupid|idiot|dumb|useless)\b',
    r'\b(hate|kill|die)\b',
    r'\b(shut up|go away)\b',
]

def _is_harassment(self, text):
    for pattern in HARASSMENT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            self._log_incident("harassment", text)
            return True
    return False
```

### Prompt Injection Detection

```python
INJECTION_PATTERNS = [
    r'ignore (previous|all|above) instructions',
    r'you are now',
    r'pretend to be',
    r'act as if',
    r'system prompt',
]

def _is_prompt_injection(self, text):
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            self._log_incident("prompt_injection", text)
            return True
    return False
```

---

## 4.9 Complete RAG Flow

```
User: "What are MSc AI fees for international students?"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ROUTER AGENT                                                   │
│  • Guardrails: PASS                                            │
│  • Intent: fee_question                                        │
│  • Student type: international                                 │
│  • Student level: postgraduate                                 │
│  • Next action: rag                                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RAG AGENT                                                      │
│                                                                 │
│  1. Build enhanced query:                                       │
│     "MSc AI fees international student postgraduate"           │
│                                                                 │
│  2. Generate embedding via OpenAI                              │
│                                                                 │
│  3. Hybrid search:                                             │
│     • Vector: Find semantically similar chunks                 │
│     • Keyword: Find chunks with "fee", "£", "AI"              │
│     • Combine and re-rank                                      │
│                                                                 │
│  4. Top 5 chunks retrieved:                                    │
│     [MSc AI page, Fees page, Scholarships page, ...]          │
│                                                                 │
│  5. Build prompt:                                              │
│     System: "You are a friendly admissions assistant..."       │
│     User: "Context: [chunks] Question: What are fees?"         │
│                                                                 │
│  6. Call Claude Sonnet (temperature=0.7)                       │
│                                                                 │
│  7. Return answer + sources                                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RESPONSE                                                       │
│                                                                 │
│  Answer: "MSc AI fees for international students are           │
│           £24,300/year. You may be eligible for scholarships   │
│           worth £4,000-£7,000. Need help with the application?"│
│                                                                 │
│  Sources: ["https://stir.ac.uk/courses/msc-ai/"]              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4.10 Code Reading Exercise

### Exercise 1: Trace the Search

Open `scripts/enhanced_rag.py` and find:
1. `HybridSearch.search()` method
2. The SQL query for vector search (uses `<->` operator)
3. How results are combined in `_combine_results()`

### Exercise 2: Understand the Prompt

In `scripts/enhanced_rag.py`, find:
1. `AnswerGenerator._build_system_prompt()` method
2. The "CORE RULES" section
3. How student type affects the prompt

### Exercise 3: Follow the State

In `scripts/conversational_system.py`, find:
1. `ConversationState` TypedDict
2. How `RouterAgent` modifies state
3. How `RAGAgent` uses state to build queries

---

## 📖 Continue to Part 5

**Next:** Open `05_FRONTEND_UI.md` to understand the React chat interface.

---

## Quick Reference

| Component | File | Purpose |
|-----------|------|---------|
| HybridSearch | `enhanced_rag.py` | Vector + keyword search |
| AnswerGenerator | `enhanced_rag.py` | Claude integration |
| EnhancedRAG | `enhanced_rag.py` | Full RAG pipeline |
| RouterAgent | `conversational_system.py` | Intent + guardrails |
| RAGAgent | `conversational_system.py` | Search + answer |
| LeadCaptureAgent | `conversational_system.py` | Contact collection |
| GuardrailChecker | `guardrails.py` | Safety filters |
