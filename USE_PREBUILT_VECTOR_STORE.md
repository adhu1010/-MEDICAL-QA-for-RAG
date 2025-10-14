# Using Pre-built Vector Store

## How It Works

The Medical RAG system **automatically uses a persistent vector store**. You only need to build it once!

## Storage Location

```
medical-rag-qa/
└── vector_store/              # Persistent ChromaDB storage
    ├── chroma.sqlite3         # Metadata database
    └── [UUID]/                # Vector embeddings (50-100 MB)
```

## Build Once, Use Forever

### 1️⃣ **First Time: Build Vector Store**

```bash
# Only run this ONCE to build the vector store
python scripts/build_vector_store.py
```

**What happens:**
- Downloads and processes 16,410 medical documents
- Generates BioBERT embeddings (768-dim vectors)
- Saves to `vector_store/` directory
- Takes ~80-120 minutes on CPU

### 2️⃣ **Every Time After: Automatic Load**

When you start the backend or run tests, the system **automatically loads** the pre-built vector store:

```python
# This automatically loads existing vector store
from backend.retrievers.vector_retriever import VectorRetriever

retriever = VectorRetriever()  # ✓ Loads from vector_store/ if exists
```

**No rebuild needed!** The system:
- ✅ Checks if `vector_store/` exists
- ✅ Loads the existing collection (`get_or_create_collection`)
- ✅ Ready to query in seconds

## Quick Status Check

Check if you already have a pre-built vector store:

```bash
python check_vector_status.py
```

**Output if already built:**
```
Collection: medical_documents
Document Count: 16,410
Progress: 100% (16,410 / 16,410)

✅ Vector store build complete!
   → Ready to test with: python test_vector_retrieval.py
```

**Output if not built yet:**
```
Document Count: 0
Progress: 0% (Build not started)

⚠️  Vector store is empty
   → Run: python scripts/build_vector_store.py
```

## Using Pre-built Vector Store

### Option 1: Use Current Build (Recommended)

Once the current build completes, the vector store is **permanently saved**:

```bash
# Just start using it!
python test_vector_retrieval.py    # Test retrieval
python backend/main.py              # Start API server
```

### Option 2: Share Pre-built Vector Store

You can copy a pre-built vector store from another machine:

```bash
# On machine with built vector store
zip -r vector_store.zip vector_store/

# On new machine
unzip vector_store.zip
# Now vector_store/ contains all embeddings
```

**Important**: Both machines must use the **same embedding model** (`dmis-lab/biobert-base-cased-v1.2`)

### Option 3: Download Pre-computed Embeddings (Advanced)

If you have pre-computed embeddings from external sources:

```python
from backend.retrievers.vector_retriever import VectorRetriever

retriever = VectorRetriever()

# Add pre-computed embeddings
retriever.collection.add(
    embeddings=your_precomputed_embeddings,  # List of 768-dim vectors
    documents=your_documents,
    metadatas=your_metadata,
    ids=your_ids
)
```

## When to Rebuild

You only need to rebuild if:

❌ **Don't rebuild if:**
- Backend restarts
- Running tests
- Querying the system
- Server crashes

✅ **Rebuild only if:**
- Adding new medical documents to the dataset
- Changing the embedding model
- Vector store corrupted/deleted
- Upgrading ChromaDB version (sometimes)

## Incremental Updates

To add new documents without rebuilding everything:

```python
from backend.retrievers.vector_retriever import VectorRetriever

retriever = VectorRetriever()  # Loads existing collection

# Add new documents (appends to existing)
new_docs = ["New medical document 1", "New medical document 2"]
new_metadata = [{"source": "manual", "date": "2025-10-14"}] * 2
new_ids = ["doc_new_1", "doc_new_2"]

retriever.add_documents(
    documents=new_docs,
    metadatas=new_metadata,
    ids=new_ids
)

# Vector store now contains: 16,410 + 2 = 16,412 documents
```

## Backend Auto-Load

When you start the backend, it automatically loads the vector store:

```bash
python backend/main.py
```

**Logs:**
```
INFO | Loading embedding model: dmis-lab/biobert-base-cased-v1.2
INFO | Embedding model loaded successfully
INFO | ChromaDB initialized with PersistentClient at vector_store
INFO | Loaded ChromaDB collection: medical_documents
```

**No build required!** The backend is ready to answer questions immediately.

## Performance Comparison

| Action | First Time (Build) | After Build (Load) |
|--------|-------------------|-------------------|
| **Time** | ~80-120 minutes | ~5-10 seconds |
| **CPU Usage** | High (embedding generation) | Low (just loading) |
| **Memory** | ~4-6 GB | ~2-3 GB |
| **Disk I/O** | High (writing embeddings) | Low (reading metadata) |

## Verification

To verify the vector store is working:

```bash
# 1. Check status
python check_vector_status.py

# 2. Test retrieval
python test_vector_retrieval.py

# 3. Query API (if backend running)
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is diabetes?"}'
```

## Current Build Status

The vector store is **currently being built** in the background:

- ✅ Loaded 16,410 documents
- 🔄 Processing batch 1/4 (documents 1-5,000)
- ⏳ Remaining: batches 2-4 (11,410 documents)

Once complete, you'll **never need to rebuild again** unless you add new documents or change the model!

## Summary

**Key Points:**
1. ✅ Vector store is **automatically persistent** (saved to disk)
2. ✅ Build **once**, use **forever**
3. ✅ Backend **auto-loads** on startup (no manual intervention)
4. ✅ Can **copy** vector store between machines (same model required)
5. ✅ Can **incrementally add** new documents without rebuilding

**You don't need to rebuild every time!** The current build (once finished) will be reused automatically. 🎉
