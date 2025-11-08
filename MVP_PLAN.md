# 🚀 Stirling Chat MVP - Revised Plan (3 Weeks)

## 📋 Requirements Summary

- **Timeline**: 3 weeks (build, test, improve)
- **Queries**: ~50/day (low volume)
- **Priority**: Best quality responses over cost
- **Response Style**: Friendly, step-by-step, with relevant page links
- **Hosting**: Local laptop (no cloud costs)
- **Pages to crawl**: ~50 priority pages (exclude news)
- **Code style**: Minimalistic, well-commented

---

## 🎯 LLM Choice for MVP

### Recommended: **Claude 3 Haiku**

**Why Claude 3 Haiku:**

| Factor                        | Claude 3 Haiku   | Claude 3.5 Sonnet | GPT-4o mini  |
| ----------------------------- | ---------------- | ----------------- | ------------ |
| **Cost (50 queries/day)**     | ~$1.35/month     | ~$16/month        | ~$0.50/month |
| **Response Quality**          | Good                     | Excellent         | Good        |
| **Speed**                     | Fastest                  | Fast              | Fast        |
| **Following Instructions**    | Good                     | Superior          | Good        |
| **Context Window**            | 200K tokens              | 200K tokens       | 128K tokens |
| **Cost Efficiency**           | 🏆 Best                  | Expensive         | Good        |

**Cost Calculation (50 queries/day):**
```
Monthly queries: 50 × 30 = 1,500
Input tokens: 1,500 × 2,100 = 3.15M tokens
Output tokens: 1,500 × 300 = 0.45M tokens

Claude 3 Haiku:
- Input: 3.15M × $0.25 / 1M = $0.79
- Output: 0.45M × $1.25 / 1M = $0.56
- Total: $1.35/month

For MVP testing (low volume): ~$0.50-1/month
```

**Decision**: Use **Claude 3 Haiku** for cost-efficient, fast responses. At $1.35/month for 50 queries/day, it's extremely economical while maintaining good quality with:
- 200K context window (same as Sonnet)
- Fast response times
- Good instruction following
- Tool calling support
- Vision capabilities

**Upgrade Path**: Can easily switch to Claude 3.5 Sonnet later if higher quality is needed.

---

## 📊 Website Analysis

### Stirling University Structure

Based on research:

- **Undergraduate courses**: 170+ programs
- **Postgraduate courses**: 90+ programs
- **Total course pages**: ~260+
- **Supporting pages**: ~100+ (admissions, fees, campus, etc.)

### Priority Pages for MVP (~50 pages)

#### Category 1: Course Overview (10 pages)

1. `/courses/` - Main course listing
2. `/courses/ug/` - Undergraduate courses
3. `/courses/pg-taught/` - Postgraduate taught
4. `/study/undergraduate/` - UG overview
5. `/study/postgraduate/` - PG overview
6. `/study/undergraduate/flexible-undergraduate-degrees/` - Flexible degrees
7. `/study/postgraduate/choosing-a-course/` - Choosing PG course
8. `/study/online-learning/` - Online learning
9. Top 2 most popular undergraduate programs (e.g., Business, Computer Science)

#### Category 2: Admissions & Requirements (10 pages)

10. `/study/how-to-apply/` - Application process
11. `/study/undergraduate/entry-requirements/` - UG entry requirements
12. `/study/postgraduate/entry-requirements/` - PG entry requirements
13. `/study/international-students/` - International students
14. `/study/fees-and-funding/` - Fees overview
15. `/study/undergraduate/fees-and-funding/` - UG fees
16. `/study/postgraduate/fees-and-funding/` - PG fees
17. `/study/scholarships/` - Scholarships
18. `/study/how-to-apply/ucas/` - UCAS applications
19. `/study/how-to-apply/direct-applications/` - Direct applications

#### Category 3: Key Dates & Deadlines (5 pages)

20. `/study/key-dates/` - Academic calendar
21. `/study/undergraduate/key-dates/` - UG key dates
22. `/study/postgraduate/key-dates/` - PG key dates
23. `/study/open-days/` - Open days
24. `/study/clearing/` - Clearing (if applicable)

#### Category 4: Campus & Student Life (10 pages)

25. `/about/` - About Stirling
26. `/about/campus/` - Campus overview
27. `/about/accommodation/` - Accommodation
28. `/student-life/` - Student life
29. `/student-life/sport/` - Sports facilities
30. `/student-life/clubs-and-societies/` - Clubs
31. `/about/location/` - Location
32. `/student-life/support/` - Student support
33. `/student-life/careers/` - Careers service
34. `/about/facilities/` - Facilities

#### Category 5: Top Programs (15 pages)

35-49. Top 15 most popular/relevant programs:

- Business & Management
- Computer Science
- Psychology
- Marketing
- Nursing
- Education
- Sports Studies
- Finance
- Law
- Media & Communications
- Biology
- Environmental Science
- English
- History
- Social Work

#### Category 6: Contact & Support (1 page)

50. `/contact/` - Contact information

---

## 🔬 Embedding Model Selection: Deep Semantic Understanding

### Current Status: URLs Organized
✅ **1,206 URLs** categorized across 7 sections
✅ **Ready for crawling** with FireCrawl

### Recommended Embedding Model: **OpenAI text-embedding-3-small**

**Why OpenAI text-embedding-3-small:**

| Factor | OpenAI text-embedding-3-small | Cohere Embed v3 | Winner |
|--------|-------------------------------|-----------------|--------|
| **Cost** | $0.02 per 1M tokens | $0.10 per 1M tokens | 🏆 OpenAI |
| **Semantic Quality** | Good - reliable for RAG | Excellent | Cohere |
| **Dimensions** | 1536 | 1024 | OpenAI (more detail) |
| **Context Understanding** | Good for general content | Superior for educational | Balanced |
| **API Reliability** | Excellent, proven at scale | Excellent | Tie |
| **Integration** | Simple, well-documented | Simple | Tie |
| **Production Ready** | Yes, widely used | Yes | Tie |

**Cost Calculation for 1,206 Pages:**
```
Average page: ~2,000 words = ~2,700 tokens
Chunks per page: 2,700 / 800 = 3.4 chunks
Total chunks: 1,206 × 3.4 = ~4,100 chunks
Total tokens: 4,100 × 800 = 3,280,000 tokens

OpenAI text-embedding-3-small Cost: 3.28M × $0.02 / 1M = $0.07
```

**Decision**: Use **OpenAI text-embedding-3-small** for cost efficiency. At $0.07 for all embeddings, it's the most economical choice while still providing good semantic understanding for:
- Course descriptions and comparisons
- Admission requirements
- Policy information
- Cross-referencing related content

**Why This Still Works Well:**
- OpenAI's model has been proven in thousands of RAG applications
- 1536 dimensions provide detailed semantic representation
- Combined with 800-token chunks, we maintain semantic completeness
- Claude 3 Haiku will handle the reasoning during generation

**Alternative Options** (for future consideration):
1. **Cohere Embed v3** - Better semantic depth, $0.33 total cost
2. **BGE-M3** (Open Source, MIT License) - Free, multilingual, 1024-d
3. **stella_en_1.5B_v5** (Open Source, MIT License) - Free, English-only, 1024-d

### Why Deep Semantic Understanding Matters

For a university chatbot, users ask complex questions like:
- "What's the difference between BSc Computer Science and BSc Software Engineering?"
- "Can I transfer from undergraduate to postgraduate with my current qualifications?"
- "What scholarships am I eligible for as an international student from Pakistan?"

These require:
✅ **Nuanced comparison** between similar programs
✅ **Multi-hop reasoning** across different pages (courses → requirements → scholarships)
✅ **Context preservation** for eligibility criteria
✅ **Semantic similarity** beyond keyword matching

OpenAI text-embedding-3-small provides solid semantic understanding, and combined with our 800-token chunking strategy and Claude 3 Haiku for generation, we'll achieve high-quality, cost-efficient responses.

---

## 🕷️ FireCrawl Batch Scraping Strategy

### Implementation Approach: Category-Based Batches

**Why Batch by Category:**
- ✅ Better error isolation (one category fails, others succeed)
- ✅ Easier progress tracking
- ✅ Organized output structure
- ✅ Can prioritize critical content first
- ✅ Easier to re-run failed batches

**Processing Order (by priority):**
1. **Courses** (267 URLs) - Core content, highest query volume
2. **Study** (113 URLs) - Admissions, critical for prospective students
3. **Student Life** (344 URLs) - Campus experience, engagement
4. **About** (261 URLs) - University information
5. **Scholarships** (70 URLs) - Financial aid
6. **Research** (85 URLs) - Research programs
7. **International** (66 URLs) - International students

**Total**: 1,206 URLs

### FireCrawl API Details

**Pricing:**
- Free Tier: 500 credits/month
- Starter Plan: $20/month for 3,000 credits
- Our Need: 1,206 credits (one-time)

**Recommendation**: Use Starter Plan ($20) for initial crawl

**Output Structure:**
```
data/
├── crawled/
│   ├── about/           # 261 markdown files
│   ├── courses/         # 267 markdown files
│   ├── international/   # 66 markdown files
│   ├── research/        # 85 markdown files
│   ├── scholarships/    # 70 markdown files
│   ├── student-life/    # 344 markdown files
│   ├── study/           # 113 markdown files
│   └── metadata/        # JSON metadata per category
└── urls/                # Existing URL lists
```

### FireCrawl Features We'll Use

1. **Batch Scraping API** - Process multiple URLs concurrently
2. **Markdown Output** - Clean, structured content
3. **Metadata Extraction** - Title, description, URL automatically
4. **Error Handling** - Built-in retry logic
5. **Progress Tracking** - Monitor crawl status

**Sample Code:**
```python
from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key="fc-YOUR-API-KEY")

# Batch scrape by category
job = firecrawl.batch_scrape(
    urls=course_urls,  # List from courses.txt
    formats=["markdown"],
    poll_interval=2,
    wait_timeout=300
)

print(f"Status: {job.status}, Completed: {job.completed}/{job.total}")
```

---

## 🧩 Optimal Chunking Strategy

### Recommended: 800 Tokens with 200 Token Overlap

**Why 800 Tokens (~600 words)?**

1. **Semantic Completeness**
   - Covers full course descriptions
   - Complete admission requirement sections
   - Entire FAQ answers
   - Full date/deadline information

2. **Embedding Model Compatibility**
   - Well within Cohere's limits (512-4096 tokens)
   - Optimal for semantic understanding
   - Balances context vs. precision

3. **Retrieval Efficiency**
   - Retrieve 5-8 chunks = 4,000-6,400 tokens
   - Leaves 195K+ tokens for Claude 3 Haiku's response
   - Provides sufficient context without noise

4. **Overlap Benefits (200 tokens = 25%)**
   - Prevents information loss at boundaries
   - Maintains semantic continuity
   - Improves retrieval accuracy

### Content Type Analysis

| Content Type | Typical Length | Why 800 Tokens Works |
|--------------|----------------|----------------------|
| Course descriptions | 600-1000 words | Captures full program details |
| Admission requirements | 400-800 words | Complete requirement lists |
| Dates/Deadlines | 300-600 words | Full calendar with context |
| Campus facilities | 600-1000 words | Detailed descriptions |
| FAQ items | 400-700 words | Q&A with full context |
| Staff profiles | 500-800 words | Bio + contact + expertise |

### Alternative Configurations

| Chunk Size | Overlap | Use Case | Pros | Cons |
|------------|---------|----------|------|------|
| 500 tokens | 100 | Short queries | Precise | May split context |
| **800 tokens** ✅ | **200** | **Balanced** | **Complete context** | **Optimal** |
| 1200 tokens | 300 | Long-form | Full sections | May include noise |

---

## 🗄️ Database Schema (PostgreSQL + pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    full_content TEXT NOT NULL,
    crawled_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    token_count INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient similarity search
CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX ON chunks(document_id);
CREATE INDEX ON documents(category);
CREATE INDEX ON documents(source_url);
```

---

## 🏗️ Simplified Architecture

```
User Question
    ↓
FastAPI Backend (Local)
    ↓
RAG Agent (LangChain)
    ↓
├─→ PostgreSQL + pgvector (Local) → Retrieve relevant chunks
└─→ Claude 3 Haiku API → Generate step-by-step answer
    ↓
Response with:
- Friendly step-by-step answer
- Relevant page links (ordered by relevance)
```

---

## 📁 Minimal Project Structure

```
stirling_chat/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app (100 lines)
│   │   ├── config.py            # Configuration (30 lines)
│   │   ├── database.py          # DB setup (50 lines)
│   │   ├── models.py            # SQLAlchemy models (80 lines)
│   │   ├── crawler.py           # FireCrawl integration (100 lines)
│   │   ├── embeddings.py        # Embedding generation (80 lines)
│   │   ├── rag_agent.py         # RAG logic (150 lines)
│   │   └── prompts.py           # System prompts (50 lines)
│   ├── requirements.txt         # Dependencies
│   └── .env                     # Environment variables
├── frontend/
│   ├── index.html               # Simple chat UI (100 lines)
│   ├── style.css                # Styling (80 lines)
│   └── app.js                   # Chat logic (150 lines)
├── data/
│   └── crawled_pages.json       # Cached crawled data
├── scripts/
│   ├── setup_db.py              # Database initialization (50 lines)
│   └── crawl.py                 # Run crawler (30 lines)
└── MVP_PLAN.md                  # This file
```

**Total Code**: ~1,000 lines (minimal, focused)

---

## 📅 3-Week Timeline

### Week 1: Infrastructure & Data (Nov 1-7)

#### Day 1-2: Setup

- [ ] Install PostgreSQL locally with pgvector
- [ ] Set up Python environment
- [ ] Create minimal project structure
- [ ] Configure environment variables
- [ ] Test database connection

#### Day 3-4: Data Collection

- [ ] Get FireCrawl API key (Starter plan $20)
- [ ] Implement `firecrawl_scraper.py` with category-based batching
- [ ] Test with 10 URLs from courses category
- [ ] Run full crawl for all 1,206 URLs (prioritize: Courses → Study → Student Life)
- [ ] Verify markdown files saved correctly by category
- [ ] Save metadata JSON for each category

#### Day 5-7: Data Processing & Embeddings

- [ ] Update `process_markdown.py` with 800-token chunks, 200-token overlap
- [ ] Process all markdown files into chunks (~4,100 chunks expected)
- [ ] Implement `generate_embeddings.py` using OpenAI text-embedding-3-small
- [ ] Generate embeddings for all chunks (Cost: ~$0.07)
- [ ] Implement `load_to_db.py` for PostgreSQL storage
- [ ] Load documents and chunks into database
- [ ] Create vector indexes for similarity search
- [ ] Test similarity search with sample queries

**Deliverable**: Database with 1,206 pages (~4,100 chunks) vectorized and searchable

---

### Week 2: RAG Agent & API (Nov 8-14)

#### Day 8-9: RAG Agent

- [ ] Create system prompt for friendly, step-by-step responses
- [ ] Implement retrieval logic (top 5 chunks)
- [ ] Integrate Claude 3 Haiku
- [ ] Test with sample questions

#### Day 10-11: Response Formatting

- [ ] Format responses with step-by-step structure
- [ ] Extract and rank relevant page URLs
- [ ] Add source citations
- [ ] Test response quality

#### Day 12-14: FastAPI Backend

- [ ] Create `/chat` endpoint
- [ ] Add conversation memory (simple in-memory)
- [ ] Implement error handling
- [ ] Test API with Postman/curl

**Deliverable**: Working API that answers questions

---

### Week 3: Frontend & Testing (Nov 15-21)

#### Day 15-16: Simple Frontend

- [ ] Create basic HTML chat interface
- [ ] Add CSS styling (clean, modern)
- [ ] Implement JavaScript for API calls
- [ ] Add loading states

#### Day 17-18: Testing & Refinement

- [ ] Test with 20+ real questions
- [ ] Refine system prompt based on responses
- [ ] Fix bugs and edge cases
- [ ] Optimize response quality

#### Day 19-20: Improvements

- [ ] Add conversation history display
- [ ] Improve UI/UX based on testing
- [ ] Add helpful features (copy response, clear chat)
- [ ] Performance optimization

#### Day 21: Final Testing & Documentation

- [ ] End-to-end testing
- [ ] Write simple user guide
- [ ] Document setup process
- [ ] Prepare demo

**Deliverable**: Fully functional MVP ready for demonstration

---

## 💻 Local Setup (No Cloud Costs)

### System Requirements

- **OS**: Windows (your laptop)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **Python**: 3.11+
- **PostgreSQL**: 15+

### Installation Steps

```bash
# 1. Install PostgreSQL (Windows)
# Download from: https://www.postgresql.org/download/windows/
# During install, enable pgvector extension

# 2. Create database
psql -U postgres
CREATE DATABASE stirling_chat;
\c stirling_chat
CREATE EXTENSION vector;

# 3. Set up Python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. Configure .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/stirling_chat
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key_for_embeddings
FIRECRAWL_API_KEY=your_firecrawl_key

# 5. Crawl website (1,206 URLs)
python scripts/firecrawl_scraper.py

# 6. Process markdown files
python scripts/process_markdown.py

# 7. Generate embeddings
python scripts/generate_embeddings.py

# 8. Load into database
python scripts/load_to_db.py

# 9. Run backend
python -m uvicorn app.main:app --reload

# 10. Open frontend
# Open frontend/index.html in browser
```

---

## 🎨 System Prompt for Friendly, Step-by-Step Responses

```python
SYSTEM_PROMPT = """You are a friendly AI assistant for the University of Stirling.

Your role is to help prospective students, current students, and visitors find 
information about courses, admissions, campus life, and university services.

RESPONSE STYLE:
1. Be warm and conversational
2. Break down answers into clear steps when appropriate
3. Use bullet points for clarity
4. Include specific details (dates, requirements, fees)
5. Always provide relevant page links for further exploration

RESPONSE FORMAT:
- Start with a direct answer to the question
- If the answer has multiple parts, use numbered steps
- End with "For more details, visit:" followed by relevant links (ordered by relevance)
- If you don't have the information, say so politely and suggest who to contact

CONTEXT FROM UNIVERSITY WEBSITE:
{context}

CONVERSATION HISTORY:
{chat_history}

USER QUESTION: {question}

Provide a helpful, step-by-step answer with relevant page links.
"""
```

### Example Response Format

**User**: "How do I apply for Computer Science?"

**AI Response**:

```
Great question! Here's how to apply for Computer Science at Stirling:

**Step 1: Check Entry Requirements**
For BSc Computer Science, you'll typically need:
- A-levels: ABB-BBB
- Higher: AABBB
- IB: 32 points

**Step 2: Choose Your Application Route**
- UK/EU students: Apply through UCAS
- International students: You can apply directly or through UCAS
- Application deadline: January 31st for September entry

**Step 3: Prepare Your Application**
You'll need:
- Personal statement
- Academic references
- Proof of English language (if applicable)

**Step 4: Submit and Track**
After submission, you can track your application through UCAS Track or 
our applicant portal.

**For more details, visit:**
1. Computer Science BSc - https://www.stir.ac.uk/courses/ug/computer-science/
2. How to Apply - https://www.stir.ac.uk/study/how-to-apply/
3. Entry Requirements - https://www.stir.ac.uk/study/undergraduate/entry-requirements/
4. UCAS Applications - https://www.stir.ac.uk/study/how-to-apply/ucas/

Need help with your application? Contact admissions@stir.ac.uk
```

---

## 💰 Total MVP Cost

### One-Time Costs

- PostgreSQL: $0 (local install)
- Development tools: $0 (free)

### One-Time Costs
- FireCrawl Starter Plan: $20 (for 1,206 pages)
- OpenAI Embeddings: $0.07 (one-time for 1,206 pages)

**Total One-Time**: ~$20.07

### Monthly Costs (Testing Phase)

- Claude 3 Haiku API: ~$0.50-1/month (50 queries/day)
- PostgreSQL: $0 (local install)

**Total Monthly**: ~$0.50-1 during testing

### After Approval (Scaling to 500 queries/day)
- Claude 3 Haiku API: ~$13/month (or upgrade to Sonnet ~$160/month for higher quality)
- Hosting (if moving to cloud): ~$50/month
- Total: ~$63/month (Haiku) or ~$210/month (Sonnet)

---

## ✅ Success Criteria

### Week 1

- [ ] Database set up with pgvector
- [ ] 50 pages crawled and vectorized
- [ ] Similarity search working

### Week 2

- [ ] RAG agent generates quality responses
- [ ] API endpoint functional
- [ ] Responses include step-by-step format and links

### Week 3

- [ ] Chat interface working
- [ ] Tested with 20+ questions
- [ ] Response quality meets expectations
- [ ] Ready for demo

---

## 🎯 Key Differences from Original Plan

| Aspect             | Original Plan          | MVP Plan                    |
| ------------------ | ---------------------- | --------------------------- |
| **Timeline** | 3-4 weeks              | 3 weeks (focused)           |
| **LLM**      | GPT-4o mini (cheap)    | Claude 3 Haiku (cost-efficient) |
| **Hosting**  | Cloud VPS              | Local laptop                |
| **Pages**    | 1000+                  | 50 priority pages           |
| **Queries**  | 1000/day               | 50/day                      |
| **Code**     | Full-featured          | Minimalistic                |
| **Frontend** | React widget           | Simple HTML/JS              |
| **Cost**     | $35/month | $5-8/month |                             |
| **Focus**    | Scalability            | Quality & Speed             |

---

## 📝 Next Steps

1. **Approve this plan** or request changes
2. **Get API keys**:
   - Anthropic Claude: https://console.anthropic.com/
   - OpenAI (for embeddings): https://platform.openai.com/
   - FireCrawl: https://firecrawl.dev/
3. **Start Week 1**: Set up local environment
4. **Daily check-ins**: Review progress and adjust

---

## 🚀 Ready to Start?

This plan is optimized for:

- ✅ Cost-efficient quality (Claude 3 Haiku)
- ✅ 3-week timeline
- ✅ Local hosting (no cloud costs)
- ✅ Minimal, clean code
- ✅ 50 priority pages
- ✅ Friendly, step-by-step responses

**Let me know if you approve, and we'll start building!**
