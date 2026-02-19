# 🩺 Medical RAG QA System - Complete Documentation

**All-in-one comprehensive guide for the Agentic RAG Medical Question Answering System.**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Running the System](#running-the-system)
6. [Frontend-Backend Integration](#frontend-backend-integration)
7. [API Reference](#api-reference)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Development](#development)
11. [Deployment](#deployment)
12. [FAQ & Support](#faq--support)

---

## Overview

The **Medical RAG QA System** is an intelligent question-answering platform that combines:

- 🤖 **Large Language Models (LLMs)** - BioGPT, GPT-4, FLAN-T5
- 🔍 **Hybrid Retrieval** - Vector search (ChromaDB/FAISS) + Knowledge Graphs (Neo4j/NetworkX)
- 🧠 **Medical NER** - scispaCy for entity recognition and UMLS mapping
- ✅ **Safety Reflection** - Validates answers for accuracy and safety
- 👥 **Dual User Modes** - Doctor (detailed + citations) and Patient (simplified)
- 📊 **Evaluation Suite** - BLEU, ROUGE, and Faithfulness metrics

### Key Features

- ✅ **Agentic Decision Layer** - Intelligently chooses retrieval strategies
- ✅ **Real-time Chat Interface** - Firebase-based persistent chat history
- ✅ **REST API** - Complete backend API with interactive docs
- ✅ **Safety-First** - Built-in content filtering and validation
- ✅ **Production Ready** - Docker support, error handling, logging
- ✅ **Fully Integrated** - Frontend ↔ Backend seamlessly connected

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- ChromaDB with FAISS (Vector embeddings)
- Neo4j or NetworkX (Knowledge graphs)
- BioBERT (Medical embeddings)
- BioGPT or OpenAI GPT (LLM generation)
- Guardrails AI (Safety validation)

**Frontend:**
- React 18 with Vite
- Firebase Firestore (Chat history)
- Tailwind CSS (Styling)
- Lucide React (Icons)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (Reverse proxy)
- Uvicorn (ASGI server)

---

## Quick Start (5 Minutes)

### Prerequisites

```bash
# Check requirements
python --version           # Python 3.9 or higher
node --version             # Node.js 16 or higher
npm --version              # npm 7 or higher
```

### Step 1: Install Backend Dependencies

```bash
cd medical-rag-qa
pip install -r requirements.txt
```

**On Windows with build errors:**
```bash
pip install -r requirements-minimal.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your preferences (optional API keys)
```

### Step 3: Prepare Data

```bash
python scripts/download_data.py        # Download sample medical data
python scripts/build_vector_store.py   # Build semantic search index
python scripts/build_knowledge_graph.py # Build knowledge graph
```

### Step 4: Run the System

**Option A: Automated (Both Frontend & Backend)**

```bash
./start-dev.sh              # Linux/macOS
# or
start-dev.bat               # Windows
```

**Option B: Manual (Two Terminals)**

Terminal 1 (Backend):
```bash
cd medical-rag-qa
pyenv shell 3.12.0          # Use Python 3.12 (avoid 3.14 compatibility issues)
python -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd medical-rag-qa/frontend
npm install
npm run dev
```

**Option C: Docker (All-in-One)**

```bash
cd medical-rag-qa
docker-compose up --build
```

### Step 5: Access the System

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Try It Out

Ask a medical question:
- "What are the side effects of Metformin?"
- "What is Type 2 Diabetes?"
- "How does Aspirin work?"

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│                  (Vite + React 18)                          │
│              Firebase Firestore Chat History                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTP REST API (Fetch)
                 │ CORS Enabled
                 ↓
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Python)                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Query Preprocessing                                     │
│     ├─ NER (Named Entity Recognition)                      │
│     ├─ Entity Extraction                                   │
│     └─ Query Type Classification                           │
│                                                              │
│  2. Agentic Orchestration                                   │
│     ├─ Intent Detection                                    │
│     ├─ Retrieval Strategy Selection                        │
│     └─ Mode Detection (Patient/Doctor)                     │
│                                                              │
│  3. Hybrid Retrieval                                        │
│     ├─ Vector Store Search (Semantic)                      │
│     │  └─ ChromaDB + FAISS, Cosine Similarity             │
│     ├─ Knowledge Graph Query (Structured)                  │
│     │  └─ Neo4j or NetworkX                               │
│     └─ Fusion (RRF + Reranking)                            │
│                                                              │
│  4. Evidence Processing                                     │
│     ├─ Context Assembly                                    │
│     ├─ Source Citation                                     │
│     └─ Metadata Enrichment                                 │
│                                                              │
│  5. Answer Generation                                       │
│     ├─ LLM Selection (BioGPT, GPT-4, FLAN-T5)             │
│     ├─ Prompt Engineering                                  │
│     ├─ Temperature Control                                 │
│     └─ Token Management                                    │
│                                                              │
│  6. Safety Validation                                       │
│     ├─ Hallucination Detection                             │
│     ├─ Safety Reflection                                   │
│     ├─ Citation Verification                               │
│     └─ Content Filtering                                   │
│                                                              │
│  7. Response Formatting                                     │
│     ├─ Confidence Scoring                                  │
│     ├─ Metadata Assembly                                   │
│     └─ JSON Serialization                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
         │                    │                     │
         ↓                    ↓                     ↓
    ┌────────────┐  ┌─────────────────┐  ┌──────────────────┐
    │ Vector DB  │  │ Knowledge Graph │  │  External APIs   │
    │ (ChromaDB) │  │ (Neo4j/NetworkX)│  │  (OpenAI, etc.)  │
    └────────────┘  └─────────────────┘  └──────────────────┘
```

### Data Flow

```
User Question
    ↓
[1] Preprocessing: NER, Entity Extraction
    ↓
[2] Agent Decision: Select retrieval strategy
    ├─ Vector-only (conceptual)
    ├─ KG-only (factoid)
    └─ Hybrid (complex)
    ↓
[3] Retrieval: Get evidence from multiple sources
    ├─ Vector Store (semantic search)
    ├─ Knowledge Graph (structured facts)
    └─ Fusion (combine & rerank)
    ↓
[4] Generation: Create answer from evidence
    └─ LLM processes context + question
    ↓
[5] Validation: Safety checks
    └─ Hallucination detection
    └─ Citation verification
    ↓
[6] Response: Return to frontend
    ├─ Answer text
    ├─ Confidence score
    ├─ Sources & citations
    ├─ Metadata
    └─ Safety status
    ↓
[7] Storage: Save to Firebase
    └─ Chat history preserved
```

---

## Installation & Setup

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.9+ (avoid 3.14 - compatibility issues) |
| **Node.js** | 16+ |
| **RAM** | 8GB minimum (16GB recommended) |
| **Disk** | 10GB (for models + data) |
| **OS** | Windows, Linux, macOS |

### Installation Steps

#### 1. Clone Repository

```bash
cd /path/to/workspace
git clone <repository-url>
cd medical-rag-qa
```

#### 2. Install Backend Dependencies

```bash
# Using Python 3.12 (recommended)
pyenv shell 3.12.0

# Install requirements
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Troubleshooting:**

If you encounter issues:

```bash
# Minimal installation
pip install -r requirements-minimal.txt

# Force reinstall with no cache
pip install --no-cache-dir -r requirements.txt

# Check what's installed
pip list | grep -E "fastapi|chromadb|pydantic"
```

#### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env (optional)
# - API keys (OPENAI_API_KEY, HUGGINGFACE_API_KEY)
# - Model selection
# - Port configuration
# - Database connections
```

**Key Environment Variables:**

```env
# API Keys
OPENAI_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG_MODE=True

# Models
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2
LLM_MODEL=microsoft/BioGPT-Large
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=512

# Retrieval
TOP_K_VECTOR=5
TOP_K_KG=3
SIMILARITY_THRESHOLD=0.7

# Safety
ENABLE_SAFETY_REFLECTION=True
ENABLE_CONTENT_FILTER=True

# Data
DATA_DIR=./data
MEDQUAD_PATH=./data/medquad
VECTOR_STORE_PATH=./vector_store
```

#### 5. Prepare Data

```bash
# Download sample medical data
python scripts/download_data.py

# Build vector store (embeddings)
python scripts/build_vector_store.py

# Build knowledge graph
python scripts/build_knowledge_graph.py

# Verify setup
python check_vector_status.py
```

---

## Running the System

### Option 1: Automated Start (Recommended)

```bash
# Linux/macOS
./start-dev.sh

# Windows
start-dev.bat
```

This will:
- ✅ Check prerequisites
- ✅ Install missing dependencies
- ✅ Start backend on port 8000
- ✅ Start frontend on port 5173

### Option 2: Manual Start - Backend Only

```bash
cd medical-rag-qa
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be at: http://localhost:8000

**API Endpoints:**
- Health: GET /api/health
- Ask Question: POST /api/ask
- Preprocess: POST /api/preprocess
- Stats: GET /api/stats
- Docs: GET /docs

### Option 3: Manual Start - Frontend Only

```bash
cd medical-rag-qa/frontend
npm run dev
```

Frontend will be at: http://localhost:5173

### Option 4: Docker

```bash
cd medical-rag-qa

# Build and start all services
docker-compose up --build

# Access at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

### Option 5: Production Server

```bash
# Using Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000

# Or using uvicorn with workers
python -m uvicorn backend.main:app --workers 4 --host 0.0.0.0 --port 8000
```

---

## Frontend-Backend Integration

### Architecture Overview

The frontend is a **React Vite application** that communicates with the backend via **HTTP REST API**.

```
React Frontend (5173)
        ↓ Fetch API
        ↓ JSON
        ↓
FastAPI Backend (8000)
```

### API Client

**Location:** `frontend/src/api.js`

The frontend uses a centralized API client for all backend communication:

```javascript
import { apiClient } from './api';

// Ask a medical question
const response = await apiClient.askQuestion(
  'What are the side effects of aspirin?',
  'auto'  // 'auto', 'patient', or 'doctor'
);

// Health check
const health = await apiClient.healthCheck();

// Preprocess query
const processed = await apiClient.preprocessQuery(question);

// Get statistics
const stats = await apiClient.getStats();
```

### Environment Configuration

**Frontend:** `frontend/.env.local`

```env
# Local development
VITE_API_BASE_URL=http://localhost:8000

# Production
VITE_API_BASE_URL=https://api.your-domain.com
```

### CORS Configuration

The backend has CORS enabled for frontend communication:

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all (configurable for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For Production:** Restrict to specific domain:

```python
allow_origins=[
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com",
]
```

### Response Format

All backend responses follow a consistent structure:

```json
{
  "question": "What is aspirin used for?",
  "answer": "Aspirin is...",
  "mode": "patient",
  "confidence": 0.87,
  "sources": [
    {
      "title": "Document Title",
      "content": "Source text...",
      "score": 0.95
    }
  ],
  "safety_validated": true,
  "metadata": {
    "retrieval_strategy": "hybrid",
    "entities_found": 5,
    "evidence_count": 3,
    "query_type": "factoid"
  }
}
```

---

## API Reference

### Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "preprocessor": "ready",
    "agent": "ready",
    "generator": "ready",
    "safety_reflector": "ready"
  }
}
```

### Ask Question

**Endpoint:** `POST /api/ask`

**Request:**
```json
{
  "question": "What is Metformin used for?",
  "mode": "auto"
}
```

**Parameters:**
- `question` (string, required): Medical question
- `mode` (string, optional): "auto", "patient", or "doctor"

**Response:**
```json
{
  "question": "What is Metformin used for?",
  "answer": "Metformin is an oral diabetes medication...",
  "mode": "patient",
  "confidence": 0.92,
  "sources": [
    {
      "title": "Metformin Overview",
      "content": "Metformin is the first-line medication...",
      "score": 0.96
    }
  ],
  "safety_validated": true,
  "metadata": {
    "retrieval_strategy": "hybrid",
    "entities_found": 3,
    "evidence_count": 2,
    "query_type": "factoid"
  }
}
```

### Preprocess Query

**Endpoint:** `POST /api/preprocess`

**Request:**
```json
{
  "question": "What is Type 2 Diabetes?",
  "mode": "auto"
}
```

**Response:**
```json
{
  "original_question": "What is Type 2 Diabetes?",
  "entities": ["Type 2 Diabetes"],
  "detected_mode": "patient",
  "suggested_strategy": "vector",
  "query_type": "definitional"
}
```

### System Statistics

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "vector_store": {
    "collection_count": 8,
    "embedding_dim": 768
  },
  "knowledge_graph": {
    "nodes": 9,
    "edges": 7
  }
}
```

### Example API Calls

**Using curl:**

```bash
# Ask a question
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the side effects of Aspirin?",
    "mode": "patient"
  }'

# Check health
curl "http://localhost:8000/api/health"

# Get statistics
curl "http://localhost:8000/api/stats"
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/ask",
    json={
        "question": "What is Diabetes?",
        "mode": "patient"
    }
)

answer = response.json()
print(answer['answer'])
print(f"Confidence: {answer['confidence']}")
```

**Using JavaScript:**

```javascript
const response = await fetch('http://localhost:8000/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: 'What is Diabetes?',
        mode: 'patient'
    })
});

const data = await response.json();
console.log(data.answer);
```

---

## Configuration

### .env File

**Location:** `medical-rag-qa/.env`

**Template:** See `.env.example`

### Key Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `APP_PORT` | 8000 | Backend server port |
| `DEBUG_MODE` | True | Enable debug logging |
| `EMBEDDING_MODEL` | `dmis-lab/biobert-base-cased-v1.2` | Embedding model |
| `LLM_MODEL` | `microsoft/BioGPT-Large` | LLM for generation |
| `TOP_K_VECTOR` | 5 | Number of vector results |
| `TOP_K_KG` | 3 | Number of KG results |
| `SIMILARITY_THRESHOLD` | 0.7 | Relevance threshold |

### Performance Tuning

```env
# For faster responses (less accurate)
TOP_K_VECTOR=3
SIMILARITY_THRESHOLD=0.5
LLM_MAX_TOKENS=256

# For better quality (slower)
TOP_K_VECTOR=10
SIMILARITY_THRESHOLD=0.9
LLM_MAX_TOKENS=1024
```

### Model Selection

```env
# BioBERT (Medical, Recommended)
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2

# All-MiniLM (Fast, General)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM Options
LLM_MODEL=microsoft/BioGPT-Large              # Medical
LLM_MODEL=google/flan-t5-base                 # Fast
LLM_MODEL=gpt-4                               # Best (requires API key)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Python 3.14 Incompatible with spacy/pydantic"

**Symptom:** `pydantic.v1.errors.ConfigError: unable to infer type for attribute "REGEX"`

**Solution:** Use Python 3.12 instead

```bash
pyenv shell 3.12.0
python -m uvicorn backend.main:app --reload
```

**Prevention:** Avoid Python 3.14 for now

#### Issue 2: "Module Not Found" Errors

**Solution:** Reinstall dependencies

```bash
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

#### Issue 3: "Port Already in Use"

**Solution:** Use different port

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Change port in .env or command
python -m uvicorn backend.main:app --port 8001
```

#### Issue 4: "CORS Error" in Browser Console

**Solution:** Verify backend URL in frontend

```bash
# Check frontend/.env.local
cat frontend/.env.local

# Should show:
# VITE_API_BASE_URL=http://localhost:8000
```

#### Issue 5: "Out of Memory"

**Solution:** Use smaller models

```env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=google/flan-t5-base
LLM_MAX_TOKENS=256
```

#### Issue 6: "No Medical Documents Found"

**Solution:** Build vector store

```bash
python scripts/download_data.py
python scripts/build_vector_store.py
```

#### Issue 7: "Generic Template Answers"

**Symptom:** Always same generic answer, 0% confidence

**Root Cause:** Vector similarity metric issue (L2 instead of cosine)

**Solution:** Already fixed in codebase, but verify:

```bash
python check_vector_status.py
```

Should show: "Metric: cosine"

### Debugging

#### Check Logs

```bash
# View application logs
tail -f logs/app.log

# Filter for errors
grep ERROR logs/app.log
```

#### Test API

```bash
# Health check
curl http://localhost:8000/api/health

# Test with question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}'
```

#### Browser Console

Press `F12` in browser, check Console tab for:
- Network errors
- CORS issues
- JavaScript errors

#### Run Tests

```bash
python scripts/test_pipeline.py
python check_vector_status.py
```

---

## Development

### Project Structure

```
medical-rag-qa/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration
│   ├── models/                    # Data models
│   ├── preprocessing/             # Query NER & processing
│   ├── agents/                    # Agent orchestrator
│   ├── retrievers/                # Vector + KG retrievers
│   ├── generators/                # Answer generation
│   ├── safety/                    # Safety validation
│   ├── evaluation/                # Metrics
│   └── utils/                     # Utilities
├── frontend/
│   ├── src/
│   │   ├── api.js                # API client
│   │   └── main.jsx              # React entry
│   ├── index.html                # HTML template
│   ├── interface.jsx             # Main component
│   ├── .env.local                # Environment
│   ├── vite.config.js            # Build config
│   ├── package.json              # Dependencies
│   └── nginx.conf                # Web config
├── scripts/
│   ├── download_data.py          # Data preparation
│   ├── build_vector_store.py     # Embeddings
│   ├── build_knowledge_graph.py  # KG setup
│   ├── test_pipeline.py          # Integration tests
│   └── run.py                    # Quick start
├── data/
│   ├── medquad/                  # Medical QA
│   └── pubmed/                   # PubMed abstracts
├── vector_store/                 # Embeddings DB
├── .env                          # Configuration
├── .env.example                  # Config template
├── requirements.txt              # Backend deps
├── requirements-minimal.txt      # Minimal deps
├── docker-compose.yml            # Docker setup
├── Dockerfile                    # Backend image
├── start-dev.sh                  # Linux/Mac startup
├── start-dev.bat                 # Windows startup
├── test-integration.sh           # Integration tests
└── README.md                     # This file
```

### Code Organization

**Backend:**
- **preprocessing/** - Query analysis & NER
- **agents/** - Decision making (retrieval strategy)
- **retrievers/** - Vector store & knowledge graph search
- **generators/** - LLM answer generation
- **safety/** - Validation & filtering

**Frontend:**
- **api.js** - Centralized HTTP client
- **interface.jsx** - Main React component
- **firebase** - Real-time chat history

### Making Changes

1. **Backend changes**: Auto-reload with `--reload` flag
2. **Frontend changes**: Vite auto-refresh
3. **Config changes**: Restart server
4. **Dependency changes**: Reinstall with `pip install` or `npm install`

### Testing

```bash
# Integration test
python scripts/test_pipeline.py

# Health check
curl http://localhost:8000/api/health

# API test
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is diabetes?"}'
```

---

## Deployment

### Docker Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# With logging
docker-compose up --build -d
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Checklist

- [ ] Set `DEBUG_MODE=False` in .env
- [ ] Use Python 3.12
- [ ] Configure API keys if needed
- [ ] Restrict CORS to frontend domain
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring & logging
- [ ] Configure backup strategy
- [ ] Load test the system
- [ ] Document deployment process
- [ ] Plan disaster recovery

### Environment Variables for Production

```env
DEBUG_MODE=False
APP_HOST=0.0.0.0
APP_PORT=8000

# Security
ALLOWED_ORIGINS=https://yourdomain.com

# Performance
LLM_MAX_TOKENS=512
TOP_K_VECTOR=5

# Monitoring
LOG_LEVEL=INFO
```

---

## FAQ & Support

### Frequently Asked Questions

**Q: Can I use this for real medical advice?**

A: No. This system is for **educational and research purposes only**. Always consult qualified healthcare professionals for medical decisions.

**Q: Which Python version should I use?**

A: **Python 3.12 is recommended**. Avoid 3.14 due to spacy/pydantic compatibility issues.

**Q: How do I add more medical data?**

A: 
1. Add documents to `data/medquad/` or `data/pubmed/`
2. Run `python scripts/build_vector_store.py`
3. Restart the backend

**Q: Can I use OpenAI GPT-4 instead of BioGPT?**

A: Yes. Set in `.env`:
```env
OPENAI_API_KEY=your_key
LLM_MODEL=gpt-4
```

**Q: How do I improve answer quality?**

A:
- Use larger LLM models
- Increase `TOP_K_VECTOR` for more context
- Add more training data
- Fine-tune models on medical data
- Increase `LLM_MAX_TOKENS`

**Q: Can I use Neo4j instead of NetworkX?**

A: Yes. Configure in `.env`:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

**Q: How do I enable the React frontend?**

A: Frontend is already integrated:
```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

**Q: What if the backend won't start?**

A: Try:
1. Check Python version: `python --version` (use 3.12)
2. Reinstall dependencies: `pip install --no-cache-dir -r requirements.txt`
3. Check logs: `cat logs/app.log`
4. Test import: `python -c "import backend.main"`

**Q: How do I debug API calls?**

A: 
1. Check browser console (F12)
2. Look at network tab
3. View backend logs: `tail -f logs/app.log`
4. Test with curl: `curl http://localhost:8000/api/health`

### Getting Help

1. **Check logs:** `logs/app.log`
2. **Read documentation:** This guide
3. **Test health:** http://localhost:8000/api/health
4. **Review errors:** Browser console (F12)
5. **Run diagnostics:** `python scripts/test_pipeline.py`

### Common Commands Reference

```bash
# Installation
pip install -r requirements.txt
npm install --prefix frontend

# Data preparation
python scripts/download_data.py
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py

# Running
python -m uvicorn backend.main:app --reload
cd frontend && npm run dev

# Testing
python scripts/test_pipeline.py
curl http://localhost:8000/api/health

# Queries
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is diabetes?","mode":"patient"}'

# Docker
docker-compose up --build
docker-compose down
```

---

## Important Disclaimers

### ⚠️ Medical Disclaimer

This system is:
- ✅ For **educational and research purposes only**
- ✅ A **technology demonstration**
- ✅ **NOT for clinical use**
- ✅ **NOT a replacement for medical professionals**

### Always Consult Healthcare Professionals

When making medical decisions, always:
1. Consult qualified healthcare providers
2. Verify information with authoritative sources
3. Consider individual health conditions
4. Seek emergency help when needed

---

## Additional Resources

### Documentation Files

All documentation has been consolidated into this file. For reference, the original files were:

- README.md - Project overview
- GETTING_STARTED.md - Installation guide
- FRONTEND_BACKEND_INTEGRATION.md - API integration
- TROUBLESHOOTING.md - Issue solutions
- QUICK_START_INTEGRATION.md - 5-minute setup
- And 40+ other specific guides

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Docker Documentation](https://docs.docker.com/)

### Citation

If you use this project in research, please cite:

```bibtex
@software{medical_rag_qa_2025,
  title={Agentic RAG for Medical Question Answering},
  author={Your Team},
  year={2025},
  url={https://github.com/your-repo}
}
```

---

## Success Checklist

After setup, verify:

- [ ] Python 3.12 installed and active
- [ ] All dependencies installed successfully
- [ ] Sample data downloaded
- [ ] Vector store built successfully
- [ ] Knowledge graph initialized
- [ ] Backend starts without errors
- [ ] Frontend compiles successfully
- [ ] Health check endpoint responds: http://localhost:8000/api/health
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Frontend loads: http://localhost:5173
- [ ] Can ask medical questions
- [ ] Receiving answers with confidence scores
- [ ] Chat history saving to Firebase

---

## Quick Start Commands

Copy and paste these to get running:

```bash
# 1. Install backend
pip install -r requirements.txt

# 2. Install frontend
npm install --prefix frontend

# 3. Prepare data
python scripts/download_data.py
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py

# 4. Terminal 1: Start backend
python -m uvicorn backend.main:app --reload --port 8000

# 5. Terminal 2: Start frontend
cd frontend && npm run dev

# 6. Access
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-06 | Initial release with full integration |

---

**Last Updated:** January 6, 2026  
**Status:** ✅ Production Ready  
**Consolidated From:** 50+ documentation files

---

🎉 **You're all set! Start exploring the Medical RAG QA System!** 🩺🤖
