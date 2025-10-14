# Quick API Integration Test Guide

## 🎯 Current Status

### What's Ready:
✅ Data processed (16,407 QA pairs + 14,460 diseases)  
✅ Auto mode detection implemented  
✅ Test scripts created  
⏳ Vector store building (16,410 documents)  
⏭️ Backend not started yet  

---

## 🚀 Steps to Test API Integration

### Step 1: Wait for Vector Store (if still building)

**Check status**:
The terminal running `build_vector_store.py` should show:
```
INFO - Added 16410 documents to vector store
INFO - ✓ Vector store built successfully
```

**Estimated time**: Should complete within 5-15 minutes from now

### Step 2: Build Knowledge Graph

Once vector store is complete:

```bash
python scripts/build_knowledge_graph.py
```

**Expected output**:
```
INFO - Loading Disease Ontology
INFO - Loaded 14460 disease terms
INFO - Extracted 3000+ triples from Disease Ontology
INFO - ✓ Knowledge graph built successfully
INFO - Graph stats: 1000 nodes, 3000-5000 edges
```

**Time**: 2-5 minutes

### Step 3: Start Backend

```bash
python scripts/run.py
```

**Expected output**:
```
INFO - Loading embedding model: dmis-lab/biobert-base-cased-v1.2
INFO - Embedding model loaded successfully
INFO - ChromaDB initialized
INFO - Agent controller initialized
INFO - Loading HuggingFace model: microsoft/BioGPT-Large
INFO - Application startup complete
INFO - Uvicorn running on http://0.0.0.0:8000
```

**Backend will be available at**: http://localhost:8000

### Step 4: Run Integration Tests

In a **new terminal**:

```bash
python test_api_integration.py
```

---

## 📋 Test Coverage

The integration test will verify:

### ✅ Test 1: Health Check
- Backend is running
- All components initialized
- System version info

### ✅ Test 2: Query Preprocessing
- Entity extraction working
- Mode detection accurate
- Strategy selection correct

### ✅ Test 3: Question Answering
- Basic definitions (e.g., "What is diabetes?")
- Drug information (e.g., "Side effects of metformin?")
- Technical questions (e.g., "Pathophysiology of diabetes?")

### ✅ Test 4: Statistics
- Vector store document count
- Knowledge graph nodes/edges
- System metrics

### ✅ Test 5: Error Handling
- Empty questions rejected
- Invalid modes rejected
- Proper error messages

### ✅ Test 6: Mode Detection Accuracy
- Doctor mode for technical questions
- Patient mode for personal questions
- 80%+ accuracy target

---

## 🔍 Expected Test Output

### Successful Test Run:

```
================================================================================
MEDICAL RAG QA API - INTEGRATION TESTS
================================================================================

Backend URL: http://localhost:8000
Timeout: 30s

================================================================================
TEST 1: Health Check
================================================================================

✓ Backend is healthy
  Status: healthy
  Version: 1.0.0
  Components: {'preprocessor': 'ready', 'agent': 'ready', ...}

================================================================================
TEST 2: Query Preprocessing
================================================================================

Test Case 1: Medical professional question
Question: What is the differential diagnosis for chest pain?
✓ Preprocessing successful
  Detected mode: doctor
  Query type: complex
  Strategy: hybrid
  Entities found: 2
  Entities:
    - chest pain (SYMPTOM)
    - diagnosis (PROCEDURE)
✓ Mode detection correct: doctor

[... more tests ...]

================================================================================
TEST SUMMARY
================================================================================

  Health Check.......................................... PASS
  Query Preprocessing................................... PASS
  Question Answering.................................... PASS
  Statistics............................................ PASS
  Error Handling........................................ PASS
  Mode Detection........................................ PASS

Overall: 6/6 tests passed

✓ All tests passed! API integration working correctly.
```

---

## 🧪 Manual API Testing

### Using cURL:

**Health Check**:
```bash
curl http://localhost:8000/api/health
```

**Ask a Question**:
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is diabetes?",
    "mode": "patient"
  }'
```

**Preprocess Query**:
```bash
curl -X POST http://localhost:8000/api/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the pathophysiology of diabetes?",
    "mode": "patient"
  }'
```

**Get Statistics**:
```bash
curl http://localhost:8000/api/stats
```

### Using Python:

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Ask question
response = requests.post(
    "http://localhost:8000/api/ask",
    json={
        "question": "What are the side effects of Metformin?",
        "mode": "patient"
    }
)
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Mode: {result['mode']}")
```

### Using Browser:

1. Open: http://localhost:8000/docs
2. Interactive API documentation (Swagger UI)
3. Try out endpoints directly

---

## ⏱️ Complete Timeline

```
Now:        Vector store building (⏳ ~10-20 min remaining)
            ↓
Step 2:     Build knowledge graph (2-5 min)
            ↓
Step 3:     Start backend (1-2 min)
            ↓
Step 4:     Run tests (2-3 min)
            ↓
Complete:   Full system tested and working!

Total: ~15-30 minutes from now
```

---

## 🆘 Troubleshooting

### Vector Store Still Building?

**Check progress**:
- Look at the terminal running `build_vector_store.py`
- Should be processing 16,410 documents
- CPU usage should be high (60-100%)

**If stuck**:
- Wait 5 more minutes
- Check if CPU usage is active
- If no progress after 30 total minutes, press Ctrl+C and restart

### Knowledge Graph Build Fails?

**Error**: "Disease Ontology not found"
```bash
# Re-run data processing
python scripts/process_medquad.py
```

### Backend Won't Start?

**Error**: "Port 8000 already in use"
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Error**: "Vector store not found"
```bash
# Make sure vector store build completed
ls vector_store/
# Should see chroma.sqlite3 and .parquet files
```

### Tests Fail?

**All tests fail with connection error**:
- Backend not running → Start with `python scripts/run.py`

**Low confidence scores**:
- Normal for first run
- System is working, just being cautious

**Mode detection inaccurate**:
- Review question phrasing
- Check logs for scoring details
- Some ambiguous questions expected

---

## 📊 Success Criteria

Your system is working correctly if:

✅ Health check returns status "healthy"  
✅ Questions get answered (even if confidence varies)  
✅ Mode detection works for obvious cases (80%+)  
✅ Vector store has 16,410 documents  
✅ Knowledge graph has 1,000+ nodes  
✅ No critical errors in logs  

---

## 🎯 Next Steps After Testing

Once tests pass:

1. **Try the frontend**:
   ```bash
   cd frontend
   python -m http.server 3000
   # Open http://localhost:3000
   ```

2. **Test mode detection**:
   ```bash
   python test_auto_mode.py
   ```

3. **Add more data** (optional):
   - UMLS knowledge graph
   - PubMed API integration
   - Neo4j persistent storage

4. **Deploy** (if ready for production)

---

## 📝 Current Test Script

Created: `test_api_integration.py`

**Features**:
- 6 comprehensive test suites
- Colored terminal output
- Detailed error reporting
- Performance metrics
- Validation checks

**Run with**:
```bash
python test_api_integration.py
```

---

**Your system is almost ready! Just waiting for the vector store to finish building.** 🚀
