# 🚀 Pre-Crawled Markdown Workflow

If you already have markdown files from FireCrawl, this is your fast-track guide!

---

## ⚡ Quick Start (3 Steps)

### **Step 1: Place Your Markdown Files** (2 minutes)

Put your markdown files in the `data/crawled/` directory:

```bash
# Copy your markdown files
copy your_firecrawl_files\*.md data\crawled\

# Or if you have a JSON export
copy firecrawl_export.json data\crawled\
```

**Supported formats:**
- ✅ Individual `.md` files
- ✅ Markdown with front matter (metadata)
- ✅ JSON export from FireCrawl
- ✅ Organized in subdirectories

---

### **Step 2: Process the Files** (5-10 minutes)

```bash
# Process all markdown files
python scripts\process_markdown.py

# Or with subdirectories
python scripts\process_markdown.py --recursive

# Or specific JSON file
python scripts\process_markdown.py --format json --input data\crawled\export.json
```

**What this does:**
1. ✅ Reads all markdown/JSON files
2. ✅ Extracts metadata (URL, title, category)
3. ✅ Splits into 500-word chunks with 100-word overlap
4. ✅ Saves processed data to `data/processed/`

**Output:**
```
📊 MARKDOWN PROCESSING SUMMARY
✅ Files processed: 1,150
✅ Total chunks: 6,900
✅ Total words: 2,300,000
✅ Avg chunks/file: 6.0

📋 BREAKDOWN BY CATEGORY:
  courses_ug:    450 files | 2,700 chunks
  courses_pg:    280 files | 1,680 chunks
  admissions:    120 files |   720 chunks
  ...
```

---

### **Step 3: Generate Embeddings & Store** (10-15 minutes)

```bash
# Generate embeddings and store in database
python scripts\generate_embeddings.py

# This will:
# 1. Read processed chunks
# 2. Generate embeddings via OpenAI API
# 3. Store in PostgreSQL with pgvector
```

---

## 📁 File Format Examples

### Format 1: Simple Markdown

**File:** `computing-science.md`
```markdown
# BSc Computing Science

## Overview
Our Computing Science degree combines theoretical foundations with practical skills...

## Entry Requirements
- A-levels: ABB-BBB
- Higher: AABBB
- IB: 32 points

## Course Structure
Year 1: Introduction to Programming...
```

**Processor will auto-detect:**
- Title: "BSc Computing Science" (from first # heading)
- URL: Generated from filename
- Category: Detected from filename or content

---

### Format 2: Markdown with Front Matter (Recommended)

**File:** `computing-science.md`
```markdown
---
url: https://www.stir.ac.uk/courses/ug/computing-science/
title: BSc Computing Science
category: courses_ug
program_type: undergraduate
last_updated: 2024-10-31
---

# BSc Computing Science

Content here...
```

**Benefits:**
- ✅ Explicit metadata
- ✅ Accurate categorization
- ✅ Better search results

---

### Format 3: FireCrawl JSON Export

**File:** `firecrawl_export.json`
```json
[
  {
    "url": "https://www.stir.ac.uk/courses/ug/computing-science/",
    "title": "BSc Computing Science",
    "markdown": "# BSc Computing Science\n\n## Overview\nOur Computing Science degree...",
    "metadata": {
      "statusCode": 200,
      "crawledAt": "2024-10-31T12:00:00Z"
    }
  },
  {
    "url": "https://www.stir.ac.uk/study/undergraduate/",
    "title": "Undergraduate Study",
    "markdown": "# Undergraduate Study\n\nContent...",
    "metadata": {}
  }
]
```

**Perfect for bulk imports!**

---

## 🎯 Workflow Comparison

### Traditional Workflow (With Crawling)
```
1. Filter URLs (30 sec)
2. Crawl website (2-3 hours) ← Time consuming
3. Process markdown (10 min)
4. Generate embeddings (15 min)
5. Store in database (5 min)

Total: ~3 hours
```

### Pre-Crawled Workflow (Your Case)
```
1. Place markdown files (2 min)
2. Process markdown (10 min) ← Start here!
3. Generate embeddings (15 min)
4. Store in database (5 min)

Total: ~30 minutes ✅
```

**You save 2.5 hours!** 🎉

---

## 📊 What Gets Processed

### Metadata Extraction

**From Front Matter:**
```yaml
---
url: https://www.stir.ac.uk/page/
title: Page Title
category: courses_ug
program_type: undergraduate
---
```

**From Filename:**
```
courses_ug_computing-science.md
  ↓
category: courses_ug
slug: computing-science
```

**From Content:**
```markdown
# Page Title  ← Extracted as title
```

---

### Text Chunking

**Original content (2,500 words):**
```
Long page about Computer Science program with overview, 
requirements, modules, career prospects, etc...
```

**After chunking (500 words/chunk, 100 overlap):**
```
Chunk 1: Overview section + start of requirements (500 words)
Chunk 2: End of overview + requirements + start of modules (500 words)
Chunk 3: Modules + career prospects (500 words)
Chunk 4: Career prospects + application info (500 words)
Chunk 5: Application info + contact (500 words)
```

**Why overlap?**
- Ensures context isn't lost at chunk boundaries
- Better retrieval accuracy
- More natural answers

---

## 🔧 Advanced Options

### Custom Chunk Size

```bash
# Smaller chunks (more precise, more chunks)
python scripts\process_markdown.py --chunk-size 300 --chunk-overlap 50

# Larger chunks (more context, fewer chunks)
python scripts\process_markdown.py --chunk-size 800 --chunk-overlap 150
```

**Recommendations:**
- **Small chunks (300-400)**: Technical content, FAQs
- **Medium chunks (500-600)**: General content (default)
- **Large chunks (800-1000)**: Narrative content, guides

---

### Process Specific Categories

```bash
# Process only course files
python scripts\process_markdown.py --input data\crawled\courses\

# Process only admissions
python scripts\process_markdown.py --input data\crawled\admissions\
```

---

### Add Custom Metadata

Edit markdown files to add metadata:

```markdown
---
url: https://www.stir.ac.uk/courses/ug/computing-science/
title: BSc Computing Science
category: courses_ug
program_type: undergraduate
keywords: computer science, programming, software, IT
difficulty: intermediate
duration: 4 years
ucas_code: G400
---

Content...
```

**Benefits:**
- Better filtering in RAG
- More accurate categorization
- Richer search results

---

## 📈 Expected Processing Times

| Files | Chunks | Processing | Embeddings | Total |
|-------|--------|-----------|-----------|-------|
| 50 | 300 | 1 min | 2 min | 3 min |
| 300 | 1,800 | 3 min | 8 min | 11 min |
| 1,000 | 6,000 | 10 min | 20 min | 30 min |
| 1,500 | 9,000 | 15 min | 30 min | 45 min |

**Factors affecting speed:**
- File size
- Chunk size
- OpenAI API rate limits
- Internet connection

---

## ✅ Quality Checks

### After Processing

**1. Check processed data:**
```bash
# View summary
type data\processed\processed_data.json | more

# Check for errors
type data\processed\errors.json
```

**2. Verify chunk quality:**
```python
# Open Python
python

# Load processed data
import json
with open('data/processed/processed_data.json', 'r') as f:
    data = json.load(f)

# Check first document
doc = data['documents'][0]
print(f"Title: {doc['title']}")
print(f"Chunks: {doc['chunk_count']}")
print(f"First chunk: {doc['chunks'][0][:200]}...")
```

**3. Check categories:**
```python
# Count by category
from collections import Counter
categories = [doc['category'] for doc in data['documents']]
print(Counter(categories))
```

---

## 🐛 Troubleshooting

### "No files found"
```bash
# Check directory
dir data\crawled\

# Make sure files have .md or .json extension
# Use --recursive if files are in subdirectories
python scripts\process_markdown.py --recursive
```

---

### "Invalid markdown format"
```bash
# Check file encoding (should be UTF-8)
# Open file in notepad and save as UTF-8

# Check for special characters
# Remove or escape: <, >, &, etc.
```

---

### "Missing metadata"
**Solution:** Metadata is optional! The processor will:
1. Extract title from first `#` heading
2. Generate URL from filename
3. Auto-detect category from filename/content

**Or add front matter:**
```markdown
---
url: https://www.stir.ac.uk/page/
title: Page Title
---
```

---

### "Chunks too large/small"
```bash
# Adjust chunk size
python scripts\process_markdown.py --chunk-size 600 --chunk-overlap 120

# Test different sizes:
# 300 words = ~400 tokens (small)
# 500 words = ~670 tokens (default)
# 800 words = ~1070 tokens (large)
```

---

## 💡 Best Practices

### 1. Organize Files by Category
```
data/crawled/
├── courses/
│   ├── ug/
│   └── pg/
├── admissions/
├── campus/
└── support/
```

**Benefits:**
- Easier to manage
- Better categorization
- Can process selectively

---

### 2. Use Descriptive Filenames
```
✅ Good:
courses_ug_computing-science.md
study_undergraduate_entry-requirements.md
campus_accommodation_halls.md

❌ Bad:
page1.md
doc.md
temp.md
```

---

### 3. Add Front Matter
```markdown
---
url: https://www.stir.ac.uk/courses/ug/computing-science/
title: BSc Computing Science
category: courses_ug
program_type: undergraduate
last_updated: 2024-10-31
---
```

**Even minimal metadata helps!**

---

### 4. Clean Content Before Processing
```markdown
❌ Remove:
- Navigation menus
- Footers
- "Click here" links
- Duplicate content

✅ Keep:
- Main content
- Headings
- Lists
- Important links
```

---

## 🎯 Next Steps After Processing

### 1. Generate Embeddings
```bash
python scripts\generate_embeddings.py
```

### 2. Store in Database
```bash
python scripts\store_in_db.py
```

### 3. Test RAG Agent
```bash
python scripts\test_rag.py
```

### 4. Start Chat API
```bash
python -m uvicorn app.main:app --reload
```

---

## 📊 Complete Workflow

```
Your Markdown Files
        ↓
[Place in data/crawled/]
        ↓
[python scripts/process_markdown.py]
        ↓
data/processed/processed_data.json
        ↓
[python scripts/generate_embeddings.py]
        ↓
PostgreSQL Database (with embeddings)
        ↓
[python scripts/test_rag.py]
        ↓
Working Chatbot! 🎉
```

---

## ✅ Checklist

### Before Processing
- [ ] Markdown files in `data/crawled/`
- [ ] Files are UTF-8 encoded
- [ ] (Optional) Front matter added
- [ ] (Optional) Files organized by category

### During Processing
- [ ] Run `python scripts\process_markdown.py`
- [ ] Check for errors in output
- [ ] Review processing summary

### After Processing
- [ ] Check `data/processed/processed_data.json`
- [ ] Verify chunk count and quality
- [ ] Review any errors in `data/processed/errors.json`
- [ ] Ready for embedding generation!

---

## 🚀 Ready to Process?

**You have markdown files? Great!**

1. Place them in `data/crawled/`
2. Run `python scripts\process_markdown.py`
3. Wait ~10-15 minutes
4. Move to embedding generation!

**This workflow is 2.5 hours faster than crawling!** ⚡

---

**Questions? Check the troubleshooting section or ask for help!**
