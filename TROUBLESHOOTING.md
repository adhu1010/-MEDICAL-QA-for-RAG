# Troubleshooting Guide

## Issue: Generic Template Answers Only

### Problem
The system was returning generic template answers with 0% confidence instead of actual medical information from the knowledge base.

### Root Cause
**ChromaDB was using L2 (Euclidean) distance by default instead of cosine similarity**, causing:
- Extremely high distance values (16-39) 
- Negative confidence scores after conversion
- All documents filtered out by the similarity threshold (0.5)

### Solution
Changed the vector store to use **cosine similarity metric**:

```python
self.collection = self.chroma_client.get_or_create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"}  # Use cosine similarity instead of L2
)
```

### Results After Fix
- ✅ Proper distance values (0.07-0.17 for cosine)
- ✅ High confidence scores (0.83-0.93)
- ✅ Relevant documents retrieved successfully
- ✅ Real medical answers generated from evidence

### How to Verify It's Working

1. **Refresh your browser** (Ctrl+F5 or Cmd+Shift+R)
2. **Ask a medical question** like:
   - "What are the side effects of Metformin?"
   - "How does Metformin work?"
   - "What is the best antibiotic for sinus infection?"

3. **Expected behavior**:
   - Confidence score: 80-95% (not 0%)
   - Sources: 2-3 citations from medquad/pubmed
   - Answer: Specific medical information (not generic template)

### Test Results
```
Q: What are the side effects of Metformin?
✓ Retrieved 3 documents
✓ Confidence: 0.91
✓ Content: "Common side effects of Metformin include nausea, vomiting, stomach upset..."

Q: How does Metformin work?
✓ Retrieved 3 documents  
✓ Confidence: 0.85
✓ Content: "Metformin works primarily by decreasing glucose production in the liver..."

Q: What is the best antibiotic for sinus infection?
✓ Retrieved 3 documents
✓ Confidence: 0.93
✓ Content: "Amoxicillin is commonly prescribed as first-line therapy..."
```

## Current System Status

### Vector Store
- **Collection**: medical_documents
- **Document Count**: 8 documents
- **Sources**: 5 MedQuAD QA pairs + 3 PubMed abstracts
- **Embedding Model**: BioBERT (dmis-lab/biobert-base-cased-v1.2)
- **Similarity Metric**: Cosine (FIXED ✓)

### Knowledge Graph  
- **Implementation**: NetworkX (in-memory)
- **Nodes**: 9 sample nodes
- **Edges**: 7 sample edges
- **Status**: Using sample data (needs expansion for production)

### Backend Server
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Status**: Running with auto-reload

### Frontend Server
- **URL**: http://localhost:3000
- **Status**: Running

## If Issues Persist

### 1. Check Vector Store Stats
```bash
python scripts/test_vector_store.py
```
Should show: "Document Count: 8"

### 2. Rebuild Vector Store
```bash
python scripts/build_vector_store.py
```

### 3. Restart Backend
```bash
python scripts/run.py
```

### 4. Check Browser Console
- Press F12 in browser
- Look for network errors or CORS issues
- Verify requests are going to http://localhost:8000/api/ask

## Next Steps to Improve Answers

1. **Add more medical documents** to vector store:
   - Download MedQuAD full dataset
   - Add more PubMed abstracts
   - Include medical textbooks/guidelines

2. **Expand knowledge graph**:
   - Integrate Disease Ontology
   - Add UMLS concepts
   - Include drug-disease relationships

3. **Enable LLM generation**:
   - Install `sacremoses` for BioGPT
   - Or configure OpenAI API key for GPT-4
   - Currently using template-based fallback

4. **Install scispaCy** for better entity extraction:
   - Requires C++ build tools on Windows
   - Current fallback: regex-based extraction
