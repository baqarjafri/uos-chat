# Stirling University Chatbot

AI-powered admissions chatbot for the University of Stirling.

---

## How to Run This Project

### Step 1: Activate Python Virtual Environment

Open a terminal in the project root folder:

```bash
# Windows
venv\Scripts\activate
```

### Step 2: Start the Backend Server

```bash
cd backend
python main.py
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start the Frontend (New Terminal)

Open a **new terminal** in the project root:

```bash
cd frontend
docker-compose up -d
```

Or if Docker is not running, use npm:

```bash
cd frontend
npm install
npm run dev
```

### Step 4: Open the Application

- **Website:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

---

## Quick Start Commands (Copy-Paste)

**Terminal 1 - Backend:**

```bash
cd c:\Users\Ghulam\CascadeProjects\stirling_chat
venv\Scripts\activate
cd backend
python main.py
```

**Terminal 2 - Frontend:**

```bash
cd c:\Users\Ghulam\CascadeProjects\stirling_chat\frontend
docker-compose up -d
```

---

## Project Structure

```
stirling_chat/
├── backend/           # FastAPI server (main.py)
├── frontend/          # React app (ChatWidget, Homepage)
├── scripts/           # RAG system, guardrails, embeddings
├── database/          # SQL schema
├── data/urls/         # Scraped URL lists
└── requirements.txt   # Python dependencies
```

---

## Tech Stack

- **Backend:** FastAPI + Python
- **Frontend:** React + Vite + TailwindCSS
- **Database:** PostgreSQL + pgvector
- **LLM:** Claude Sonnet 4 (Anthropic)
- **Embeddings:** OpenAI text-embedding-3-small

---

## Troubleshooting

**Backend won't start:**

```bash
venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend won't start:**

```bash
docker restart stirling_frontend
```

**Check if database is running:**

```bash
docker ps
# Should show: stirling_chat_db
```
