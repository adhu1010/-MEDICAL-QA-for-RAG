# ChromaDB Alternatives - Complete Guide

## Overview

Your Medical RAG QA system currently uses **ChromaDB** as the vector store. This document explores alternative vector databases and how to switch between them.

---

## 🔍 Current Implementation: ChromaDB

**Location**: `backend/retrievers/vector_retriever.py` (lines 51-86)

**Current Setup**:
```python
# Initialize ChromaDB with persistence
import chromadb as chroma_lib

# Use PersistentClient for newer versions
self.chroma_client = chroma_lib.PersistentClient(
    path=str(settings.vector_store_path)
)

# Get or create collection with cosine similarity
self.collection = self.chroma_client.get_or_create_collection(
    name="medical_documents",
    metadata={"hnsw:space": "cosine"}  # Cosine similarity metric
)
```

**Characteristics**:
- ✅ Persistent storage (SQLite backend)
- ✅ Lightweight and easy to use
- ✅ No external dependencies
- ✅ Good for small to medium datasets
- ✅ Local file-based storage
- ❌ Not scalable to billions of vectors
- ❌ No distributed architecture
- ❌ Limited advanced features

---

## 📊 Vector Database Alternatives

### Comparison Table

| Feature | ChromaDB | FAISS | Pinecone | Weaviate | Milvus | Qdrant | Elasticsearch |
|---------|----------|-------|----------|----------|--------|--------|----------------|
| **Type** | Embedded | In-memory | Cloud | Hybrid | Cloud/Self | Cloud/Self | Search Engine |
| **Setup** | Easy | Easy | Requires account | Medium | Medium | Medium | Medium |
| **Cost** | Free | Free | Paid | Free | Free | Free | Free |
| **Scalability** | Low | Medium | High | High | High | High | Medium |
| **Vector Support** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Metadata Filtering** | ✓ | Limited | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Real-time Updates** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Distance Metrics** | Cosine, L2, IP | Multiple | Multiple | Multiple | Multiple | Multiple | L2, Cosine |
| **Best For** | Small projects | Research | Production | Hybrid search | Production | Production | Full-text + vectors |

---

## 🔄 Alternative 1: FAISS (Facebook AI Similarity Search)

### What it is

In-memory vector similarity search library by Meta. Fast for large-scale similarity search but requires the entire index in memory.

### Advantages
- ✅ **Fast**: Extremely fast similarity search
- ✅ **Scalable**: Handles millions of vectors efficiently
- ✅ **Free & Open-source**: No licensing costs
- ✅ **Multiple indexing methods**: IVF, HNSW, LSH, etc.
- ✅ **GPU support**: Can use CUDA for GPU acceleration
- ✅ **Well-tested**: Used by many production systems

### Disadvantages
- ❌ **In-memory only**: Entire index must fit in RAM
- ❌ **Complex indexing**: Requires careful parameter tuning
- ❌ **Rebuild required**: Can't easily add vectors after building
- ❌ **No persistence by default**: Must implement custom saving
- ❌ **No filtering**: Limited metadata filtering capabilities
- ❌ **Research-oriented**: Not as "batteries-included" as commercial solutions

### Integration Example

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class FAISSRetriever:
    def __init__(self, embedding_model="dmis-lab/biobert-base-cased-v1.2"):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.index = None
        self.documents = []
        self.document_ids = []
    
    def build_index(self, documents):
        """Build FAISS index from documents"""
        embeddings = []
        for doc in documents:
            embedding = self.embedding_model.encode(doc)
            embeddings.append(embedding)
        
        # Create FAISS index
        embeddings_array = np.array(embeddings, dtype=np.float32)
        dimension = embeddings_array.shape[1]
        
        # IVF (Inverted File) index for fast search
        quantizer = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)  # 100 clusters
        self.index.train(embeddings_array)
        self.index.add(embeddings_array)
        
        self.documents = documents
    
    def retrieve(self, query, top_k=5):
        """Search for similar documents"""
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            results.append({
                "document": self.documents[idx],
                "distance": float(distance),
                "similarity": 1 / (1 + float(distance))
            })
        return results
    
    def save_index(self, filepath):
        """Save index to disk"""
        faiss.write_index(self.index, filepath)
    
    def load_index(self, filepath):
        """Load index from disk"""
        self.index = faiss.read_index(filepath)
```

### Installation

```bash
# CPU version
pip install faiss-cpu

# GPU version (CUDA 11.x)
pip install faiss-gpu

# Or conda
conda install -c pytorch faiss-cpu
```

### When to Use FAISS
- ✅ High-performance similarity search needed
- ✅ Millions to billions of vectors
- ✅ Resource constraints on server (vertical scaling)
- ✅ Research/ML projects
- ❌ Dynamic vector insertion needed
- ❌ Complex metadata filtering required

---

## 🌐 Alternative 2: Pinecone (Cloud-Based Vector Database)

### What it is

Fully managed vector database as a service. Focus on production-grade vector search without managing infrastructure.

### Advantages
- ✅ **Fully managed**: No infrastructure to manage
- ✅ **Scalable**: Handles billions of vectors
- ✅ **Real-time updates**: Add/delete vectors instantly
- ✅ **Metadata filtering**: Rich filtering capabilities
- ✅ **Namespaces**: Organize vectors by project/customer
- ✅ **Auto-replication**: High availability built-in
- ✅ **No operational overhead**: Pinecone handles everything

### Disadvantages
- ❌ **Paid service**: Costs money (though free tier available)
- ❌ **Vendor lock-in**: Not self-hosted
- ❌ **Internet required**: API-based access
- ❌ **Latency**: Network latency for queries
- ❌ **Data privacy**: Data hosted on Pinecone servers
- ❌ **Overkill for small datasets**: Expensive for simple use cases

### Integration Example

```python
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

class PineconeRetriever:
    def __init__(self, api_key, index_name="medical-documents"):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        self.embedding_model = SentenceTransformer("dmis-lab/biobert-base-cased-v1.2")
    
    def add_documents(self, documents, metadatas=None):
        """Add documents to Pinecone"""
        vectors_to_upsert = []
        
        for i, doc in enumerate(documents):
            embedding = self.embedding_model.encode(doc)
            
            vectors_to_upsert.append((
                f"doc_{i}",  # ID
                embedding.tolist(),  # Vector
                {"text": doc, **(metadatas[i] if metadatas else {})}  # Metadata
            ))
        
        # Upsert in batches
        self.index.upsert(vectors=vectors_to_upsert, batch_size=100)
    
    def retrieve(self, query, top_k=5):
        """Search for similar documents"""
        query_embedding = self.embedding_model.encode(query)
        
        results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True
        )
        
        return results
```

### Setup

```bash
# Install Pinecone client
pip install pinecone-client

# Create account at https://www.pinecone.io
# Get API key and create index
```

### Configuration (in .env)

```bash
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=medical-documents
```

### When to Use Pinecone
- ✅ Production systems with high traffic
- ✅ Need fully managed service
- ✅ Billions of vectors needed
- ✅ Budget available for cloud services
- ❌ Self-hosted requirement
- ❌ Free tier critical
- ❌ Data sovereignty concerns

---

## 🔍 Alternative 3: Weaviate (Hybrid Search)

### What it is

Open-source, self-hosted vector database with built-in text search. Unique hybrid approach combining vector and text search.

### Advantages
- ✅ **Hybrid search**: Vector + text search together
- ✅ **Self-hosted**: Full control over data
- ✅ **Open-source**: Free and customizable
- ✅ **Cloud available**: Also available as managed service
- ✅ **Rich metadata**: Complex filtering and relationships
- ✅ **GraphQL API**: Modern query interface
- ✅ **Semantic search**: Built-in semantic capabilities

### Disadvantages
- ❌ **Complex setup**: More involved configuration
- ❌ **Resource heavy**: Requires more resources
- ❌ **Steeper learning curve**: GraphQL and Weaviate concepts
- ❌ **Smaller ecosystem**: Fewer integrations than competitors
- ❌ **Performance tuning**: Requires expertise

### Integration Example

```python
import weaviate
from sentence_transformers import SentenceTransformer

class WeaviateRetriever:
    def __init__(self, url="http://localhost:8080"):
        self.client = weaviate.Client(url)
        self.embedding_model = SentenceTransformer("dmis-lab/biobert-base-cased-v1.2")
    
    def add_documents(self, documents, metadatas=None):
        """Add documents to Weaviate"""
        for i, doc in enumerate(documents):
            embedding = self.embedding_model.encode(doc).tolist()
            
            obj = {
                "text": doc,
                **(metadatas[i] if metadatas else {})
            }
            
            self.client.data_object.create(
                data_object=obj,
                class_name="MedicalDocument",
                vector=embedding
            )
    
    def retrieve(self, query, top_k=5):
        """Hybrid search: semantic + keyword"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Hybrid query
        response = self.client.query.get(
            "MedicalDocument",
            ["text", "_additional {distance}"]
        ).with_hybrid(
            query=query,
            vector=query_embedding,
            alpha=0.5  # 50% text, 50% vector
        ).with_limit(top_k).do()
        
        return response
```

### Docker Setup

```bash
# Start Weaviate with Docker
docker run -d \
  -p 8080:8080 \
  --name weaviate \
  semitechnologies/weaviate:latest
```

### When to Use Weaviate
- ✅ Need hybrid (text + vector) search
- ✅ Self-hosted requirement
- ✅ Complex data relationships
- ✅ GraphQL API needed
- ❌ Simple use cases
- ❌ Limited DevOps resources

---

## 📦 Alternative 4: Milvus (Distributed Vector Database)

### What it is

Open-source vector database built for massive-scale applications. Designed for production at scale.

### Advantages
- ✅ **Distributed architecture**: Scales across machines
- ✅ **Production-ready**: Used by many enterprises
- ✅ **High performance**: Optimized for large scale
- ✅ **Multiple indexing**: HNSW, IVF, Scann, etc.
- ✅ **Kubernetes support**: Deploy on Kubernetes
- ✅ **Open-source**: Free and customizable

### Disadvantages
- ❌ **Complex deployment**: Requires infrastructure
- ❌ **Operational overhead**: Need to manage cluster
- ❌ **Learning curve**: Complex concepts
- ❌ **Overkill for small**: Too much for small projects
- ❌ **Resource intensive**: Requires significant resources

### Installation

```bash
# Docker Compose
docker-compose up -d  # Using provided docker-compose.yml

# Or install Python client
pip install pymilvus
```

### When to Use Milvus
- ✅ Enterprise-scale deployments
- ✅ Distributed architecture needed
- ✅ Kubernetes deployment
- ✅ Billions+ of vectors
- ❌ Small to medium projects
- ❌ Limited DevOps team

---

## ⚡ Alternative 5: Qdrant (High Performance)

### What it is

Modern vector database written in Rust. Focus on performance, scalability, and ease of use.

### Advantages
- ✅ **High performance**: Written in Rust
- ✅ **Easy deployment**: Single binary or Docker
- ✅ **Scalable**: Distributed mode available
- ✅ **Production-ready**: Used in production
- ✅ **REST & gRPC APIs**: Multiple interfaces
- ✅ **Metadata filtering**: Rich filtering
- ✅ **Snapshot support**: Easy backups

### Disadvantages
- ❌ **Newer project**: Less mature than some alternatives
- ❌ **Smaller community**: Fewer resources
- ❌ **Learning curve**: Different concepts than competitors

### Integration Example

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

class QdrantRetriever:
    def __init__(self, url="http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.embedding_model = SentenceTransformer("dmis-lab/biobert-base-cased-v1.2")
    
    def create_collection(self, collection_name="medical"):
        """Create a new collection"""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=768,  # BioBERT embedding dimension
                distance=Distance.COSINE
            ),
        )
    
    def add_documents(self, documents, metadatas=None):
        """Add documents to Qdrant"""
        points = []
        for i, doc in enumerate(documents):
            embedding = self.embedding_model.encode(doc).tolist()
            points.append(
                PointStruct(
                    id=i,
                    vector=embedding,
                    payload={"text": doc, **(metadatas[i] if metadatas else {})}
                )
            )
        
        self.client.upsert(
            collection_name="medical",
            points=points,
        )
    
    def retrieve(self, query, top_k=5):
        """Search for similar documents"""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        search_result = self.client.search(
            collection_name="medical",
            query_vector=query_embedding,
            query_filter=None,
            limit=top_k,
        )
        
        return search_result
```

### Docker Setup

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### When to Use Qdrant
- ✅ Good balance of simplicity and power
- ✅ Self-hosted requirement
- ✅ Production deployments
- ✅ Modern tech stack preferred
- ✓ Growing community needs

---

## 🔀 How to Switch Between Implementations

### Current Architecture

Your system currently wraps vector store operations:

```python
class VectorRetriever:
    def __init__(self, embedding_model="dmis-lab/biobert-base-cased-v1.2"):
        self.embedding_model = SentenceTransformer(embedding_model)
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(...)
    
    def retrieve(self, query, top_k=5):
        # Get embeddings and search
        results = self.collection.query(...)
        return results
```

### Switching Strategy

1. **Keep the interface same**: `VectorRetriever.retrieve()` method signature
2. **Change only the backend**: Replace ChromaDB initialization
3. **Minimal code changes**: Rest of system unaffected

### Step-by-Step Migration Example (to FAISS)

**1. Update imports**:
```python
import faiss
import numpy as np
```

**2. Replace initialization**:
```python
class VectorRetriever:
    def __init__(self, embedding_model="dmis-lab/biobert-base-cased-v1.2"):
        # Same embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Replace ChromaDB with FAISS
        self.index = None
        self.documents = []
        self.document_ids = []
```

**3. Replace add_documents()**:
```python
def add_documents(self, documents, metadatas=None, ids=None):
    """Build FAISS index from documents"""
    embeddings = np.array([
        self.embedding_model.encode(doc) 
        for doc in documents
    ], dtype=np.float32)
    
    # Create and train index
    dimension = embeddings.shape[1]
    quantizer = faiss.IndexFlatL2(dimension)
    self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
    self.index.train(embeddings)
    self.index.add(embeddings)
    
    self.documents = documents
    self.document_ids = ids or [f"doc_{i}" for i in range(len(documents))]
```

**4. Replace retrieve()**:
```python
def retrieve(self, query, top_k=5):
    """Search FAISS index"""
    query_embedding = self.embedding_model.encode(query.normalized_question)
    query_array = np.array([query_embedding], dtype=np.float32)
    
    distances, indices = self.index.search(query_array, top_k)
    
    evidences = []
    for idx, distance in zip(indices[0], distances[0]):
        confidence = max(0.0, 1.0 - distance)
        if confidence >= settings.similarity_threshold:
            evidence = RetrievedEvidence(
                source_type="vector",
                content=self.documents[idx],
                confidence=confidence,
                metadata={"id": self.document_ids[idx]}
            )
            evidences.append(evidence)
    
    return evidences
```

### Files to Modify

1. **`backend/retrievers/vector_retriever.py`**
   - Replace ChromaDB initialization
   - Update add_documents()
   - Update retrieve()
   
2. **`backend/config.py`** (optional)
   - Add new configuration for selected database
   - Vector store type setting

3. **`requirements.txt`**
   - Replace `chromadb` with `faiss-cpu` (or other)

4. **`.env`** (optional)
   - Add vector store selection or credentials

---

## 📋 Decision Matrix: Choosing Your Vector Database

```
┌─────────────────────────────────────────────────────────────────┐
│ Choose ChromaDB if:                                             │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Small to medium dataset (< 1M vectors)                        │
│ ✓ Don't want external dependencies                              │
│ ✓ Development/prototyping phase                                 │
│ ✓ Limited DevOps resources                                      │
│ ✓ File-based storage acceptable                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Choose FAISS if:                                                │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Maximum search speed needed                                   │
│ ✓ Dataset < available RAM                                       │
│ ✓ Research or prototyping                                       │
│ ✓ GPU acceleration needed                                       │
│ ✓ Simple similarity search only                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Choose Pinecone if:                                             │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Fully managed service preferred                               │
│ ✓ Billions of vectors needed                                    │
│ ✓ Budget available for cloud services                           │
│ ✓ Zero operational overhead desired                             │
│ ✓ Multi-tenant support needed                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Choose Weaviate if:                                             │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Hybrid text + vector search needed                            │
│ ✓ Self-hosted required                                          │
│ ✓ GraphQL API preferred                                         │
│ ✓ Complex data relationships                                    │
│ ✓ Semantic search with BM25                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Choose Milvus if:                                               │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Enterprise-scale deployment                                   │
│ ✓ Kubernetes environment                                        │
│ ✓ Billions+ of vectors                                          │
│ ✓ Distributed architecture needed                               │
│ ✓ High operational capacity                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Choose Qdrant if:                                               │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Best balance of simplicity and power                          │
│ ✓ Self-hosted Rust performance preferred                        │
│ ✓ Production deployments                                        │
│ ✓ Modern tech stack                                             │
│ ✓ Easy horizontal scaling                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Hybrid Approach: ChromaDB + FAISS

Your requirements.txt already includes both:

```
chromadb>=0.4.0    # Primary storage
faiss-cpu>=1.7.0   # Fast search
```

### Optimal Setup

Use ChromaDB for:
- Persistent storage
- Metadata management
- Document management

Use FAISS for:
- Fast similarity search
- GPU acceleration
- Batch operations

```python
class HybridVectorRetriever:
    def __init__(self):
        # Storage
        self.chroma_client = chromadb.PersistentClient(path="vector_store")
        self.collection = self.chroma_client.get_or_create_collection("medical")
        
        # Search
        self.faiss_index = None
        self.document_ids = []
    
    def add_documents(self, documents, metadatas=None):
        # Store in ChromaDB (persistent)
        self.collection.add(documents=documents, metadatas=metadatas)
        
        # Index in FAISS (fast search)
        embeddings = np.array([self.embed(doc) for doc in documents])
        self.faiss_index.add(embeddings)
    
    def retrieve(self, query, top_k=5):
        # Search with FAISS (fast)
        embedding = self.embed(query)
        distances, indices = self.faiss_index.search([embedding], top_k)
        
        # Get documents from ChromaDB (persistent)
        ids = [self.document_ids[i] for i in indices[0]]
        results = self.collection.get(ids=ids)
        
        return results
```

---

## 🚀 Recommendations for Your System

### Current State (Development)
- ✅ **Keep ChromaDB**: Perfect for current size (~16K documents)
- ✅ **Already works**: No need to change
- ✅ **Easy to upgrade**: Can switch later if needed

### Future Scaling (100K+ documents)
- 🔄 **Consider FAISS**: For speed boost
- 🔄 **Or upgrade to cloud**: Pinecone or Qdrant
- 🔄 **Or self-hosted**: Weaviate or Milvus

### Production Migration Path

```
Development          Small Scale         Medium Scale        Enterprise
────────────────────────────────────────────────────────────────────
ChromaDB      →      FAISS + ChromaDB →  Qdrant/Milvus  →   Pinecone
(16K docs)    →      (100K docs)     →   (1M+ docs)     →   (Billions)
```

---

## Summary

| Feature | Current (ChromaDB) | Recommendation |
|---------|-------------------|-----------------|
| **Dataset size** | 16K documents | ✅ Adequate |
| **Search speed** | Good | ✅ Adequate |
| **Scalability** | Limited | Upgrade for 100K+ |
| **Ease of use** | Easy | ✅ Best in class |
| **Self-hosted** | ✅ Yes | ✅ Preferred |
| **Cost** | Free | ✅ Best for budget |
| **Production ready** | ✅ Yes | ✅ Proven |

**Action**: Keep ChromaDB for now. Plan migration to FAISS or Qdrant if you exceed 100K documents or need significant speed improvements.

