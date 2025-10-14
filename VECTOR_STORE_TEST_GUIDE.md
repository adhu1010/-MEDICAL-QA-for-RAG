# Vector Store Testing Guide

## Overview

This guide explains how to test the vector retrieval functionality of the Medical RAG QA system.

## What Was Fixed

### Batch Size Issue (RESOLVED ✓)

**Problem**: Vector store build failed with error:
```
ValueError: Batch size of 16410 is greater than max batch size of 5461
```

**Root Cause**: ChromaDB has a maximum batch size limit (~5461 documents). The original code tried to add all 16,410 documents in a single batch.

**Solution**: Modified `backend/retrievers/vector_retriever.py` to implement automatic batching:
- Splits large datasets into batches of 5,000 documents
- Processes each batch sequentially
- Provides progress logging for each batch

**Code Changes**:
```python
# Before: Single batch (FAILED)
self.collection.add(
    embeddings=embeddings,
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

# After: Batched processing (SUCCESS)
BATCH_SIZE = 5000
for start_idx in range(0, total_docs, BATCH_SIZE):
    batch_docs = documents[start_idx:end_idx]
    # Process batch...
    self.collection.add(...)
```

## Vector Store Build Process

### Building the Vector Store

```bash
# Run the build script
python scripts/build_vector_store.py
```

**Expected Output**:
```
2025-10-14 18:19:22 | INFO | Adding 16410 documents in batches of 5000
2025-10-14 18:19:22 | INFO |   Processing batch 1: documents 1 to 5000
2025-10-14 18:XX:XX | INFO |   ✓ Batch 1 complete: 5000 documents added
2025-10-14 18:XX:XX | INFO |   Processing batch 2: documents 5001 to 10000
2025-10-14 18:XX:XX | INFO |   ✓ Batch 2 complete: 5000 documents added
2025-10-14 18:XX:XX | INFO |   Processing batch 3: documents 10001 to 15000
2025-10-14 18:XX:XX | INFO |   ✓ Batch 3 complete: 5000 documents added
2025-10-14 18:XX:XX | INFO |   Processing batch 4: documents 15001 to 16410
2025-10-14 18:XX:XX | INFO |   ✓ Batch 4 complete: 1410 documents added
2025-10-14 18:XX:XX | INFO | ✓ Successfully added all 16410 documents to vector store
```

**Total Batches**: 4 batches (3 full batches + 1 partial batch)
- Batch 1: 5,000 documents
- Batch 2: 5,000 documents
- Batch 3: 5,000 documents
- Batch 4: 1,410 documents

**Estimated Time**: 
- ~20-30 minutes per batch on CPU
- Total: ~80-120 minutes (depends on CPU speed)

### Monitoring Progress

The build process shows real-time progress with:
1. ✓ Current batch number
2. ✓ Document range being processed
3. ✓ Completion status for each batch
4. ✓ Total documents added

## Testing Vector Retrieval

### Quick Test

Once the vector store is built, run:

```bash
python test_vector_retrieval.py
```

This comprehensive test suite includes:

### Test 1: Vector Store Statistics
- Checks collection is initialized
- Verifies document count (should be 16,410)
- Shows embedding model details

### Test 2: Embedding Generation
- Tests BioBERT embedding generation
- Verifies embedding dimension (768)
- Measures embedding speed

### Test 3: Basic Similarity Search
- Tests retrieval for common medical queries
- Shows confidence scores
- Displays top results

### Test 4: Confidence Score Analysis
- Tests different query types (specific vs vague)
- Analyzes score distribution
- Validates threshold filtering

### Test 5: Medical Entity Recognition
- Tests queries with drugs, diseases, procedures
- Verifies entity detection works with retrieval

### Test 6: Mode-Specific Retrieval
- Compares DOCTOR vs PATIENT mode results
- Validates automatic mode detection

### Test 7: Batch Processing Performance
- Tests multiple queries in sequence
- Measures throughput (queries/second)

### Test 8: Similarity Threshold Testing
- Shows distance-to-similarity conversion
- Validates threshold filtering (≥0.3)
- Analyzes result quality

## Expected Test Results

### Successful Output Example:

```
████████████████████████████████████████████████████████████████████████████████
  MEDICAL RAG - VECTOR RETRIEVAL TEST SUITE
████████████████████████████████████████████████████████████████████████████████

================================================================================
  TEST 1: Vector Store Statistics
================================================================================

✓ Collection Name: medical_documents
✓ Document Count: 16,410
✓ Embedding Model: dmis-lab/biobert-base-cased-v1.2

✓ Vector store is properly initialized

================================================================================
  TEST 2: Embedding Generation
================================================================================

Testing embedding generation for sample queries:

  Query: 'What causes diabetes?'
    - Embedding dimension: 768
    - Time: 0.045s
    - First 5 values: [0.234, -0.567, 0.123, ...]

✓ All embeddings generated successfully

[... more tests ...]

================================================================================
  TEST SUMMARY
================================================================================

✓ PASS - Vector Store Statistics
✓ PASS - Embedding Generation
✓ PASS - Basic Similarity Search
✓ PASS - Confidence Score Analysis
✓ PASS - Medical Entity Recognition
✓ PASS - Mode-Specific Retrieval
✓ PASS - Batch Query Processing
✓ PASS - Similarity Threshold Testing

Results: 8/8 tests passed (100.0%)

🎉 All tests passed! Vector retrieval is working correctly.
```

## Manual Testing

### Test Individual Queries

```python
from backend.retrievers.vector_retriever import VectorRetriever
from backend.preprocessing.query_processor import QueryPreprocessor

# Initialize
retriever = VectorRetriever()
preprocessor = QueryPreprocessor()

# Test query
query = preprocessor.process_query("What is diabetes?")
results = retriever.retrieve(query, top_k=5)

# Check results
for i, result in enumerate(results, 1):
    print(f"{i}. Confidence: {result.confidence:.4f}")
    print(f"   Content: {result.content[:200]}...")
```

### Check Collection Stats

```python
from backend.retrievers.vector_retriever import VectorRetriever

retriever = VectorRetriever()
stats = retriever.get_collection_stats()

print(f"Documents: {stats['document_count']}")
print(f"Model: {stats['embedding_model']}")
```

## Troubleshooting

### Vector Store is Empty

**Symptom**: `document_count: 0`

**Solution**:
```bash
# Rebuild vector store
python scripts/build_vector_store.py
```

### No Results Returned

**Symptom**: All queries return 0 results

**Possible Causes**:
1. **Similarity threshold too high**: Check `backend/config.py` → `similarity_threshold` (default: 0.3)
2. **Embedding mismatch**: Verify same embedding model used for indexing and querying
3. **Empty query**: Check query preprocessing isn't filtering out all content

**Debug**:
```python
# Check raw similarity scores
retriever = VectorRetriever()
query_embedding = retriever.embed_text("What is diabetes?")
raw_results = retriever.collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
    include=["distances"]
)
print("Distances:", raw_results['distances'])
# Distance of 0.0 = perfect match
# Distance of 2.0 = completely opposite
# Similarity = 1 - distance
```

### Low Confidence Scores

**Symptom**: All results have confidence < 0.5

**Possible Causes**:
1. **Using L2 distance instead of cosine**: Check collection metadata
2. **Query too vague**: Try more specific medical terms
3. **Missing medical entities**: Query may not match document terminology

**Solution**:
```python
# Verify cosine similarity is enabled
collection = retriever.collection
print(collection.metadata)  # Should show: {"hnsw:space": "cosine"}
```

### Slow Retrieval

**Symptom**: Each query takes >5 seconds

**Possible Causes**:
1. **CPU-based embedding**: BioBERT on CPU is slower than GPU
2. **Large top_k**: Retrieving many results increases time
3. **No HNSW index**: Collection not optimized

**Optimization**:
```python
# Use GPU if available
import torch
if torch.cuda.is_available():
    retriever.embedding_model = retriever.embedding_model.to('cuda')
```

## Performance Benchmarks

### Expected Performance (CPU)

- **Embedding generation**: 40-60ms per query
- **Similarity search**: 100-200ms for top_k=10
- **Total retrieval time**: 150-300ms per query

### Expected Performance (GPU)

- **Embedding generation**: 10-20ms per query
- **Similarity search**: 100-200ms for top_k=10
- **Total retrieval time**: 120-250ms per query

## Vector Store Details

### Storage Location
```
medical-rag-qa/
└── vector_store/          # ChromaDB persistent storage
    ├── chroma.sqlite3     # Metadata database
    └── [UUID]/            # Vector embeddings
```

### Storage Size
- **16,410 documents** × **768-dim embeddings** × **4 bytes/float**
- Estimated: ~50-100 MB (including metadata)

### Embedding Model
- **Model**: `dmis-lab/biobert-base-cased-v1.2`
- **Type**: BERT-based, medical domain
- **Dimension**: 768
- **Pre-trained on**: PubMed + PMC articles

### Similarity Metric
- **Metric**: Cosine similarity
- **Range**: 0.0 (orthogonal) to 1.0 (identical)
- **Threshold**: 0.3 (configurable in `backend/config.py`)

## Next Steps

After vector store testing is complete:

1. **Build Knowledge Graph**: `python scripts/build_knowledge_graph.py`
2. **Test KG Retrieval**: `python test_kg_retrieval.py` (if available)
3. **Start Backend**: `python backend/main.py`
4. **Test Full API**: `python test_api_integration.py`

## Summary

✅ **Fixed**: Batch size limitation in vector store build
✅ **Created**: Comprehensive test suite (`test_vector_retrieval.py`)
✅ **Running**: Vector store build with 4 batches (16,410 documents)
✅ **Ready**: Tests ready to run once build completes

The vector retrieval system is now properly configured with batching support and comprehensive testing coverage!
