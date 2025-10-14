# 🚀 Quick Reference Guide

## Common Commands

### Setup & Installation

```bash
# Complete automated setup
python scripts/setup.py

# Manual installation
pip install -r requirements.txt
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz

# Download data
python scripts/download_data.py

# Build vector store
python scripts/build_vector_store.py

# Build knowledge graph
python scripts/build_knowledge_graph.py
```

### Running the System

```bash
# Quick start (recommended)
python scripts/run.py

# Manual start
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# With Docker
docker-compose up --build

# Serve frontend
python -m http.server 3000 --directory frontend
```

### Testing

```bash
# Run integration tests
python scripts/test_pipeline.py

# Test API health
curl http://localhost:8000/api/health

# Test query
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the side effects of Metformin?", "mode": "patient"}'
```

---

## API Quick Reference

### Main Endpoint

**Ask a Question:**
```bash
POST /api/ask
{
  "question": "Your medical question",
  "mode": "patient"  # or "doctor"
}
```

**Response:**
```json
{
  "answer": "Generated answer...",
  "confidence": 0.85,
  "sources": ["source1", "source2"],
  "safety_validated": true
}
```

### Other Endpoints

```bash
GET  /api/health       # System health check
POST /api/preprocess   # Query analysis only
GET  /api/stats        # System statistics
GET  /docs             # Interactive API docs
```

---

## Configuration Quick Tweaks

### Change Embedding Model (.env)
```bash
# BioBERT (best quality, slower)
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2

# MiniLM (faster, smaller)
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Change LLM Model (.env)
```bash
# BioGPT (medical specialized)
LLM_MODEL=microsoft/BioGPT-Large

# FLAN-T5 (general purpose)
LLM_MODEL=google/flan-t5-base

# OpenAI (requires API key)
OPENAI_API_KEY=sk-your-key-here
```

### Adjust Retrieval (.env)
```bash
TOP_K_VECTOR=5              # More = slower but more context
TOP_K_KG=3                  # Knowledge graph results
SIMILARITY_THRESHOLD=0.7    # Lower = more results
```

---

## Troubleshooting Quick Fixes

### "Module not found" errors
```bash
pip install -r requirements.txt --force-reinstall
```

### "scispaCy model not found"
```bash
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz
```

### "ChromaDB error"
```bash
rm -rf vector_store/
python scripts/build_vector_store.py
```

### "No data found"
```bash
python scripts/download_data.py
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py
```

### "Server won't start"
```bash
# Check port 8000 is free
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# Kill process if needed
# Then restart
```

### "Out of memory"
```bash
# Use smaller models in .env
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=google/flan-t5-base
```

---

## File Locations

### Code
- Backend: `backend/`
- Frontend: `frontend/index.html`
- Scripts: `scripts/`

### Data
- MedQuAD: `data/medquad/`
- PubMed: `data/pubmed/`
- Vector Store: `vector_store/`

### Configuration
- Environment: `.env`
- Example: `.env.example`
- Config: `backend/config.py`

### Logs
- Application: `logs/app.log`

### Documentation
- Overview: `README.md`
- Setup: `SETUP_GUIDE.md`
- API: `API_DOCUMENTATION.md`
- Architecture: `ARCHITECTURE.md`
- Summary: `PROJECT_SUMMARY.md`

---

## Example Questions to Try

### Patient Mode
```
What are the side effects of Metformin?
What is Type 2 Diabetes?
What is the best antibiotic for sinus infection?
What are the symptoms of sinusitis?
How does Metformin work?
```

### Doctor Mode
```
Explain the mechanism of action of Metformin in Type 2 Diabetes
What are the pharmacodynamics of amoxicillin in bacterial sinusitis?
Compare doxycycline and amoxicillin for sinusitis treatment
What are the contraindications for Metformin?
```

---

## URLs to Remember

When server is running:

- **API Base:** http://localhost:8000
- **Health Check:** http://localhost:8000/api/health
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Frontend:** Open `frontend/index.html` or http://localhost:3000

---

## Python API Usage

### Quick Example
```python
import requests

response = requests.post("http://localhost:8000/api/ask", json={
    "question": "What are the side effects of Metformin?",
    "mode": "patient"
})

result = response.json()
print(result["answer"])
print(f"Confidence: {result['confidence']}")
print(f"Sources: {', '.join(result['sources'])}")
```

### With Error Handling
```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/ask",
        json={"question": "Your question", "mode": "patient"},
        timeout=30
    )
    response.raise_for_status()
    
    result = response.json()
    print(f"Answer: {result['answer']}")
    
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
```

---

## Docker Quick Commands

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f backend

# Rebuild specific service
docker-compose build backend
```

---

## Environment Variables Cheat Sheet

```bash
# Required
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2
LLM_MODEL=microsoft/BioGPT-Large

# Optional (for advanced features)
OPENAI_API_KEY=sk-...
HUGGINGFACE_API_KEY=hf_...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Tuning
TOP_K_VECTOR=5
TOP_K_KG=3
SIMILARITY_THRESHOLD=0.7
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=512

# Application
DEBUG_MODE=True
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## Safety Checklist

Before deploying:
- [ ] Change default passwords
- [ ] Add authentication
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Review safety rules
- [ ] Test with edge cases
- [ ] Add monitoring
- [ ] Backup data regularly

---

## Performance Tips

### Speed Up Retrieval
- Reduce `TOP_K_VECTOR` and `TOP_K_KG`
- Use smaller embedding model
- Enable caching (future feature)

### Improve Answer Quality
- Increase `TOP_K_VECTOR` (more context)
- Use larger LLM model
- Fine-tune on domain data

### Reduce Memory Usage
- Use quantized models
- Limit `LLM_MAX_TOKENS`
- Process in batches

---

## Getting Help

1. **Check logs:** `logs/app.log`
2. **Review docs:** README.md, SETUP_GUIDE.md
3. **Test health:** http://localhost:8000/api/health
4. **Try examples:** Run `scripts/test_pipeline.py`
5. **Check requirements:** Verify all in `requirements.txt` installed

---

## One-Line Installers

### Full Setup
```bash
python scripts/setup.py && python scripts/run.py
```

### Minimal Setup (skip interactive prompts)
```bash
pip install -r requirements.txt && python scripts/download_data.py && python scripts/build_vector_store.py && python scripts/build_knowledge_graph.py
```

### Quick Test
```bash
python scripts/test_pipeline.py
```

---

## Useful Curl Commands

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Ask Question (Patient)
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is diabetes?","mode":"patient"}'
```

### Ask Question (Doctor)
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain Metformin mechanism","mode":"doctor"}'
```

### Preprocess Query
```bash
curl -X POST http://localhost:8000/api/preprocess \
  -H "Content-Type: application/json" \
  -d '{"question":"What are side effects of Metformin?"}'
```

### Get Statistics
```bash
curl http://localhost:8000/api/stats
```

---

## Keyboard Shortcuts (Frontend)

- **Enter** - Submit question
- **Ctrl+Enter** - New line in textarea
- **Click example** - Auto-fill question

---

**Keep this guide handy for quick reference! 📌**
