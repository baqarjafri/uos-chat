# 🎓 Stirling University AI Chat Agent

An intelligent RAG-powered chat agent that helps students and visitors find information about Stirling University programs, dates, and updates.

## 🌟 Features

- **Intelligent Q&A**: Answers questions about programs, dates, admissions, and university updates
- **RAG-Powered**: Uses Retrieval-Augmented Generation for accurate, grounded responses
- **Step-by-Step Responses**: Friendly, structured answers with relevant page links
- **Conversation Memory**: Maintains context across multiple questions
- **Safety Guardrails**: Validates inputs/outputs to prevent misuse
- **Local Hosting**: Runs on your laptop for MVP testing
- **Pre-Crawled Ready**: Works with existing markdown files from FireCrawl

## 🏗️ Architecture

```
Chat Interface → FastAPI Backend → RAG Agent (LangChain) → PostgreSQL + pgvector
                                                          ↘ Claude 3.5 Sonnet API
```

## 🚀 Quick Start (Pre-Crawled Workflow)

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Anthropic API key (Claude) or OpenAI API key
- Pre-crawled markdown files from FireCrawl

### Installation (30 minutes)

**1. Place your markdown files**
```bash
# Copy your FireCrawl markdown files
copy your_files\*.md data\crawled\
```

**2. Process markdown files**
```bash
python scripts\process_markdown.py
```

**3. Set up environment**
```bash
# Create .env file
DATABASE_URL=postgresql://postgres:password@localhost:5432/stirling_chat
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key_for_embeddings
```

**4. Generate embeddings and store**
```bash
python scripts\generate_embeddings.py
python scripts\store_in_db.py
```

**5. Start the chatbot**
```bash
python -m uvicorn app.main:app --reload
```

## 📚 Documentation

- **[MVP_PLAN.md](MVP_PLAN.md)** - 3-week implementation plan
- **[PRECRAWLED_WORKFLOW.md](PRECRAWLED_WORKFLOW.md)** - Guide for pre-crawled files
- **[data/crawled/README.md](data/crawled/README.md)** - File format guide

## 🎯 Project Timeline

- **Week 1-2**: Process markdown → Build RAG agent → Create API
- **Week 3**: Build chat interface → Test → Refine
- **Post-approval**: Scale to full website coverage

## 📊 Current Status

✅ Project structure created
✅ Markdown processing script ready
⏳ Waiting for markdown files to be placed
⏳ Database setup
⏳ RAG agent development

## 🤝 Contributing

This is a private project for Stirling University. For questions or issues, contact the development team.

## 📄 License

Proprietary - Stirling University
