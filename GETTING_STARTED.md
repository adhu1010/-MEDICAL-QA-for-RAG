# 🚀 Getting Started - Medical RAG QA System

## Welcome! 👋

This guide will help you get the Medical RAG QA system up and running in **under 10 minutes**.

---

## Prerequisites

- **Python 3.9 or higher** (check with `python --version`)
- **8GB RAM** recommended
- **Internet connection** (for downloading models)

---

## Installation (3 Steps)

### Step 1: Install Dependencies

**Run this FIRST** (before anything else):

```bash
python install.py
```

This will:
- ✅ Check your Python version
- ✅ Install all required packages from requirements.txt
- ✅ Download scispaCy medical NLP model (optional)
- ✅ Takes ~5-10 minutes

**What if it fails?**
```bash
# Manual installation
pip install -r requirements.txt

# Then install scispaCy model
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz
```

---

### Step 2: Prepare Data

```bash
python scripts/download_data.py
```

This creates sample medical datasets (MedQuAD + PubMed abstracts).

---

### Step 3: Build Databases

```bash
# Build vector store (semantic search database)
python scripts/build_vector_store.py

# Build knowledge graph (structured medical facts)
python scripts/build_knowledge_graph.py
```

---

## Running the System

### Option 1: Quick Start (Recommended)

```bash
python scripts/run.py
```

The server will start at **http://localhost:8000**

### Option 2: Manual Start

```bash
uvicorn backend.main:app --reload
```

---

## Using the System

### Option A: Web Interface

1. Open `frontend/index.html` in your web browser
2. Select mode (Patient or Doctor)
3. Type a medical question
4. Click "Get Answer"

**Example questions:**
- "What are the side effects of Metformin?"
- "What is Type 2 Diabetes?"
- "What is the best antibiotic for sinus infection?"

### Option B: API (Command Line)

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the side effects of Metformin?",
    "mode": "patient"
  }'
```

### Option C: Interactive API Docs

Visit **http://localhost:8000/docs** in your browser for a beautiful interactive API interface.

---

## Testing

Verify everything works:

```bash
python scripts/test_pipeline.py
```

This tests:
- ✅ Component initialization
- ✅ Query preprocessing
- ✅ Evidence retrieval
- ✅ Answer generation
- ✅ Safety validation

---

## Troubleshooting

### "ModuleNotFoundError"

**Solution:** Run installation first
```bash
python install.py
```

### "No data found"

**Solution:** Run data preparation
```bash
python scripts/download_data.py
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py
```

### "Port 8000 already in use"

**Solution:** Change port or kill existing process
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Or change port in .env
APP_PORT=8001
```

### "Out of memory"

**Solution:** Use smaller models

Edit `.env`:
```bash
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=google/flan-t5-base
```

---

## What's Next?

### Explore the System

1. **Try different questions** in Patient and Doctor modes
2. **Check the API docs** at http://localhost:8000/docs
3. **View system stats** at http://localhost:8000/api/stats
4. **Read the architecture** in ARCHITECTURE.md

### Customize Configuration

Edit `.env` file:
```bash
# Copy example
cp .env.example .env

# Edit with your preferences
# - API keys (optional)
# - Model selection
# - Retrieval settings
```

### Add Your Own Data

1. **MedQuAD:** Download full dataset
   ```bash
   git clone https://github.com/abachaa/MedQuAD.git data/medquad_full
   ```

2. **PubMed:** Use NCBI API to fetch abstracts

3. **Rebuild vector store:**
   ```bash
   python scripts/build_vector_store.py
   ```

### Deploy with Docker

```bash
# Build and run
docker-compose up --build

# Access at http://localhost:8000
```

---

## Common Workflows

### Development Workflow

```bash
# 1. Make code changes
# 2. Server auto-reloads (if using --reload)
# 3. Test changes
curl http://localhost:8000/api/health
```

### Testing Workflow

```bash
# Unit tests (future)
pytest tests/

# Integration test
python scripts/test_pipeline.py

# API test
curl -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" -d '{"question":"test"}'
```

### Production Deployment

1. **Disable debug mode** in `.env`:
   ```bash
   DEBUG_MODE=False
   ```

2. **Use production server:**
   ```bash
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Add security:**
   - Enable HTTPS
   - Add authentication
   - Configure rate limiting

---

## Learning Resources

### Documentation

- 📘 **README.md** - Project overview
- 🔧 **SETUP_GUIDE.md** - Detailed installation
- 📖 **API_DOCUMENTATION.md** - Complete API reference
- 🏗️ **ARCHITECTURE.md** - System design
- ⚡ **QUICK_REFERENCE.md** - Command cheat sheet
- 📊 **PROJECT_SUMMARY.md** - Feature list

### Code Structure

```
backend/
├── main.py              # FastAPI app - START HERE
├── preprocessing/       # Query analysis & NER
├── agents/              # Decision-making layer
├── retrievers/          # Vector + KG retrieval
├── generators/          # LLM answer generation
└── safety/              # Validation layer
```

---

## FAQ

### Q: Can I use this for real medical advice?

**A:** No! This is for educational/research only. Always consult healthcare professionals.

### Q: Which LLM is best?

**A:** 
- **BioGPT** - Best for medical terminology
- **FLAN-T5** - Faster, general purpose
- **OpenAI GPT-4** - Highest quality (requires API key)

### Q: How do I add more medical data?

**A:** 
1. Add documents to `data/medquad/` or `data/pubmed/`
2. Run `python scripts/build_vector_store.py`

### Q: Can I use Neo4j instead of NetworkX?

**A:** Yes! Configure in `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Q: How do I improve answer quality?

**A:**
- Use more/better training data
- Increase TOP_K_VECTOR for more context
- Use larger LLM models
- Fine-tune models on medical data

---

## Support

### Getting Help

1. **Check logs:** `logs/app.log`
2. **Review documentation:** See links above
3. **Test health:** http://localhost:8000/api/health
4. **Run diagnostics:** `python scripts/test_pipeline.py`

### Reporting Issues

When reporting problems, include:
- Error message
- Python version
- Operating system
- Steps to reproduce
- Relevant logs from `logs/app.log`

---

## Important Disclaimers

⚠️ **Medical Disclaimer**
This system is:
- ✅ For educational and research purposes
- ✅ A technology demonstration
- ❌ NOT for clinical use
- ❌ NOT a replacement for medical professionals

Always consult qualified healthcare providers for medical decisions.

---

## Quick Command Reference

```bash
# Installation
python install.py

# Data preparation
python scripts/download_data.py
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py

# Running
python scripts/run.py
# or
uvicorn backend.main:app --reload

# Testing
python scripts/test_pipeline.py

# Health check
curl http://localhost:8000/api/health

# Ask question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is diabetes?","mode":"patient"}'
```

---

## Success Checklist

- [ ] Python 3.9+ installed
- [ ] Dependencies installed (`python install.py`)
- [ ] Sample data downloaded
- [ ] Vector store built
- [ ] Knowledge graph built
- [ ] Server starts successfully
- [ ] Frontend opens in browser
- [ ] Can ask questions and get answers
- [ ] API docs accessible at /docs

---

**You're all set! 🎉**

Start asking medical questions and explore the system!

For more details, see [README.md](README.md) or [SETUP_GUIDE.md](SETUP_GUIDE.md).

**Happy exploring! 🩺🤖**
