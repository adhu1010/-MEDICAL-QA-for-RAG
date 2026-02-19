# ChromaDB Alternatives - Quick Reference

## Current Implementation

**Vector Database**: ChromaDB  
**Location**: `backend/retrievers/vector_retriever.py` (lines 51-86)  
**Status**: ✅ Working well for 16K documents

```python
import chromadb

# Persistent storage with cosine similarity
client = chromadb.PersistentClient(path="vector_store")
collection = client.get_or_create_collection(
    name="medical_documents",
    metadata={"hnsw:space": "cosine"}  # Cosine similarity
)
```

---

## Quick Comparison

### 5 Main Alternatives

```
┌─────────────┬────────────┬──────────┬──────────────────┐
│ Option      │ Best For   │ Cost     │ Scalability      │
├─────────────┼────────────┼──────────┼──────────────────┤
│ ChromaDB ✓  │ Small-Med  │ FREE     │ Up to 1M vectors │
│ FAISS       │ Speed      │ FREE     │ With RAM limit   │
│ Pinecone    │ Enterprise │ PAID     │ Billions         │
│ Weaviate    │ Hybrid     │ FREE     │ Self-hosted      │
│ Qdrant      │ Balanced   │ FREE     │ Distributed      │
└─────────────┴────────────┴──────────┴──────────────────┘
```

---

## ✅ FAISS (Fastest Alternative)

**Best for**: High-speed similarity search

**Setup**:
```bash
pip install faiss-cpu
```

**Code Change**:
```python
import faiss
import numpy as np

# Build index from embeddings
embeddings = np.array([embed(doc) for doc in documents], dtype=np.float32)
dimension = embeddings.shape[1]

quantizer = faiss.IndexFlatL2(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, 100)
index.train(embeddings)
index.add(embeddings)

# Search
distances, indices = index.search(query_embedding, k=5)
```

**Pros**: ⚡ Super fast, ✅ GPU support  
**Cons**: ❌ In-memory only, ❌ Requires manual persistence

---

## 🌐 Pinecone (Cloud Managed)

**Best for**: Zero-ops, production scale

**Setup**:
```bash
pip install pinecone-client
```

**Code Change**:
```python
from pinecone import Pinecone

pc = Pinecone(api_key="YOUR_KEY")
index = pc.Index("medical-documents")

# Add vectors
index.upsert(vectors=[
    ("id1", embedding1, {"text": "doc1"}),
    ("id2", embedding2, {"text": "doc2"})
])

# Search
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True
)
```

**Pros**: ✅ Fully managed, ✅ Scales billions, ✅ Zero ops  
**Cons**: 💰 Paid service, ❌ Vendor lock-in, ❌ Internet required

---

## 📦 Weaviate (Hybrid Search)

**Best for**: Text + vector search

**Setup**:
```bash
docker run -p 8080:8080 weaviate/weaviate

pip install weaviate-client
```

**Code Change**:
```python
import weaviate

client = weaviate.Client("http://localhost:8080")

# Add documents
client.data_object.create(
    data_object={"text": "doc1", "source": "medquad"},
    class_name="MedicalDocument",
    vector=embedding1
)

# Hybrid search (text + vector)
response = client.query.get(
    "MedicalDocument",
    ["text"]
).with_hybrid(
    query="What is Metformin?",
    vector=query_embedding,
    alpha=0.5  # 50% text, 50% vector
).with_limit(5).do()
```

**Pros**: ✅ Hybrid search, ✅ Self-hosted, ✅ Rich filtering  
**Cons**: ❌ Complex setup, ❌ Resource heavy

---

## ⚡ Qdrant (Balanced)

**Best for**: Modern, scalable, easy

**Setup**:
```bash
docker run -p 6333:6333 qdrant/qdrant

pip install qdrant-client
```

**Code Change**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(url="http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="medical",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

# Add documents
client.upsert(
    collection_name="medical",
    points=[
        PointStruct(id=1, vector=embedding1, payload={"text": "doc1"}),
        PointStruct(id=2, vector=embedding2, payload={"text": "doc2"})
    ]
)

# Search
results = client.search(
    collection_name="medical",
    query_vector=query_embedding,
    limit=5
)
```

**Pros**: ✅ Great balance, ✅ Easy deployment, ✅ Rust performance  
**Cons**: ⚠️ Smaller community

---

## 📊 When to Switch

### Stay with ChromaDB if:
- ✅ < 100K documents
- ✅ Search speed adequate
- ✅ No DevOps team available
- ✅ Free only solution needed

### Switch to FAISS if:
- ✅ Need maximum speed
- ✅ < 1M documents
- ✅ Similarity search only
- ✅ GPU acceleration available

### Switch to Pinecone if:
- ✅ Billions of vectors needed
- ✅ Budget available ($0.25-1 per million vectors)
- ✅ Zero operational overhead desired
- ✅ Production at scale

### Switch to Weaviate if:
- ✅ Need text + vector hybrid search
- ✅ Self-hosted required
- ✅ Complex metadata filtering
- ✅ GraphQL API needed

### Switch to Qdrant if:
- ✅ Want modern tech stack
- ✅ Self-hosted required
- ✅ Easy horizontal scaling
- ✅ Production deployment

---

## 🔄 Migration Path

```
Current (16K docs)
       │
       ↓
   ChromaDB ✓ (Keep)
       │
       ├→ Need Speed?     → FAISS
       ├→ Need Cloud?     → Pinecone
       ├→ Need Hybrid?    → Weaviate
       ├→ Need Balance?   → Qdrant
       └→ Good Enough?    → Stay! ✓
```

---

## 💡 Pro Tips

### Keep ChromaDB, Add FAISS

```python
# Use ChromaDB for storage, FAISS for search
class HybridRetriever:
    def __init__(self):
        self.storage = ChromaDB()  # Persistent
        self.search = FAISS()      # Fast
    
    def add_docs(self, docs):
        self.storage.add(docs)     # Store
        self.search.index(docs)    # Index
    
    def retrieve(self, query):
        indices = self.search.search(query)
        return self.storage.get(indices)
```

### Environment Variable to Select

```python
# In .env
VECTOR_STORE=chromadb  # or "faiss", "pinecone", "qdrant"

# In code
store = getattr(retrievers, os.getenv("VECTOR_STORE", "chromadb"))
```

---

## 🚀 Recommended Setup

| Scale | Database | Config |
|-------|----------|--------|
| **Development** | ChromaDB | Current ✓ |
| **Small Prod** (< 100K) | ChromaDB + FAISS | Hybrid |
| **Medium Prod** (100K-1M) | FAISS or Qdrant | Self-hosted |
| **Large Prod** (1M+) | Qdrant or Milvus | Distributed |
| **Enterprise** (Billions) | Pinecone | Managed |

---

## 📚 Resources

**Comprehensive Guide**: `CHROMADB_ALTERNATIVES.md` (736 lines)  
**Current Implementation**: `backend/retrievers/vector_retriever.py`  
**Configuration**: `backend/config.py`

---

## Quick Decision Tree

```
Q: How many documents do you have?
├─ < 100K? → Keep ChromaDB ✓
└─ > 100K?
    Q: Do you need managed service?
    ├─ YES → Pinecone
    └─ NO?
        Q: Do you need hybrid search?
        ├─ YES → Weaviate
        └─ NO?
            Q: Do you prefer modern tech?
            ├─ YES → Qdrant
            └─ NO → Milvus
```

---

## ✅ Bottom Line

**Your current setup is GREAT!**

ChromaDB handles your 16K medical documents perfectly. Only consider alternatives when:
- **Scaling beyond 100K docs** → Add FAISS or switch to Qdrant
- **Need fully managed** → Switch to Pinecone
- **Need text + vector hybrid** → Switch to Weaviate

For now: Keep ChromaDB, enjoy! 🎉

