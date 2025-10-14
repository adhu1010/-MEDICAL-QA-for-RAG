# Enterprise Setup Guide

This guide helps you configure the Medical RAG QA system with enterprise-grade data sources and infrastructure.

## 🏢 Enterprise Components

### 1. **UMLS Knowledge Graph** (Full Medical Ontology)
- **What**: Unified Medical Language System - comprehensive medical vocabulary
- **Size**: ~30GB (full) or ~2-5GB (subsets)
- **License**: Free (requires NIH account)
- **Includes**: SNOMED CT, RxNorm, ICD-10/11, LOINC, CPT, and 200+ vocabularies
- **Benefits**: Standardized medical terminology, comprehensive disease/drug relationships

### 2. **PubMed Central** (Medical Literature)
- **What**: Access to 7+ million biomedical research articles
- **Options**: 
  - API mode (real-time, no download)
  - Prebuilt embeddings (~100GB for full, ~20GB for subset)
- **License**: Open access
- **Benefits**: Evidence-based answers from peer-reviewed research

### 3. **Neo4j Database** (Persistent Knowledge Graph)
- **What**: Graph database for storing medical relationships
- **Size**: Depends on data loaded (typically 1-10GB)
- **License**: Community edition (free) or Enterprise
- **Benefits**: Fast graph traversal, persistent storage, scalable to billions of nodes

---

## 🚀 Quick Start

### Option 1: Interactive Setup (Recommended)

```bash
cd medical-rag-qa
python scripts/enterprise_setup.py
```

This wizard will guide you through:
1. UMLS API key configuration
2. PubMed access setup
3. Neo4j database connection
4. Automatic .env configuration

### Option 2: Manual Setup

Follow the detailed instructions below.

---

## 📋 Detailed Setup Instructions

### Step 1: Prerequisites

#### A. UMLS License (Free)

1. **Create account**: https://uts.nlm.nih.gov/uts/signup-login
2. **Accept license**: Agree to UMLS Metathesaurus License
3. **Get API key**: Profile → API Key Management
4. **Save API key**: You'll need this later

**Time**: 5-10 minutes (instant approval)

#### B. Neo4j Installation

**Windows:**
```powershell
# Download Neo4j Desktop from https://neo4j.com/download/
# Or use Chocolatey:
choco install neo4j-community

# Or use Docker:
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
```

**Verify installation:**
```bash
# Access Neo4j Browser at http://localhost:7474
# Default credentials: neo4j / neo4j (change on first login)
```

#### C. PubMed Access (Optional)

- **Email**: Required for API access (free)
- **API Key**: Optional, increases rate limit from 3 to 10 requests/sec
- **Get API key**: https://www.ncbi.nlm.nih.gov/account/

---

### Step 2: Download Data

#### Option A: Use MedQuAD (Already Downloaded) + Disease Ontology

**Current status**: MedQuAD already downloaded (~5,000 QA pairs)

```bash
# Process MedQuAD data
cd medical-rag-qa
python scripts/download_real_data.py
```

This script:
- ✓ Processes MedQuAD XML files
- ✓ Downloads Disease Ontology
- ✓ Creates JSON files for vector store and KG

**Size**: ~50MB  
**Time**: 5-10 minutes

#### Option B: Add UMLS Knowledge Graph

```bash
# Set your UMLS API key
$env:UMLS_API_KEY="your-api-key-here"

# Download UMLS concepts
python scripts/download_umls.py
```

This script:
- Downloads ~50 common medical concepts
- Fetches relationships from UMLS API
- Creates knowledge graph triples
- Saves to `data/enterprise/umls/umls_knowledge_graph.json`

**Size**: ~10MB (sample) or ~2-30GB (full, requires manual download)  
**Time**: 10-30 minutes (API mode) or several hours (full download)

#### Option C: Add PubMed Literature

```bash
# Set your email (required)
$env:PUBMED_EMAIL="your.email@example.com"

# Optional: Set API key for higher rate limits
$env:PUBMED_API_KEY="your-ncbi-api-key"

# Download PubMed articles
python scripts/download_pubmed.py
```

This script:
- Downloads ~500 medical research articles
- Extracts abstracts and metadata
- Saves to `data/enterprise/pubmed/pubmed_articles.json`

**Size**: ~50MB (500 articles) or ~100GB+ (full embeddings)  
**Time**: 20-60 minutes (API mode)

---

### Step 3: Build Vector Store

```bash
# Build vector store with all available data
python scripts/build_vector_store.py
```

This will:
1. Load MedQuAD QA pairs
2. Load PubMed articles (if available)
3. Generate BioBERT embeddings (768-dim vectors)
4. Store in ChromaDB with cosine similarity

**Expected output**:
```
✓ Vector store built successfully
Stats: {'count': 5000+, 'embeddings': True}
Location: data/vector_store
```

**Size**: ~500MB - 2GB (depending on data)  
**Time**: 30-120 minutes (depends on GPU/CPU)

---

### Step 4: Build Knowledge Graph

#### Option A: In-Memory (NetworkX) - Default

```bash
python scripts/build_knowledge_graph.py
```

Uses:
- Disease Ontology (if downloaded)
- OR UMLS (if downloaded)
- OR Sample data (fallback)

**Size**: Memory only (~100MB RAM)  
**Limitations**: Not persistent, limited to ~10,000 nodes

#### Option B: Neo4j (Persistent, Scalable)

**1. Configure Neo4j connection in .env:**

```bash
# Edit .env file
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=medical-kg
```

**2. Install Neo4j Python driver:**

```bash
pip install neo4j
```

**3. Build knowledge graph:**

```bash
python scripts/build_knowledge_graph.py --neo4j
```

This will:
- Connect to Neo4j database
- Load disease/drug relationships
- Create graph nodes and edges
- Build indexes for fast queries

**Expected output**:
```
✓ Knowledge graph built successfully
Graph stats: 15,000+ nodes, 45,000+ edges
Database: medical-kg (Neo4j)
```

**Size**: ~1-10GB (in Neo4j database)  
**Benefits**: Persistent, scalable to millions of nodes

---

### Step 5: Configure Backend

**Create/update `.env` file:**

```bash
# UMLS Configuration (if using)
UMLS_ENABLED=true
UMLS_API_KEY=your_umls_api_key
UMLS_VERSION=2024AA
UMLS_SUBSET=snomed_rxnorm

# PubMed Configuration
PUBMED_ENABLED=true
PUBMED_MODE=api
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=your_ncbi_api_key

# Neo4j Configuration
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=medical-kg

# Vector Store
VECTOR_STORE=chromadb
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2

# LLM
LLM_MODEL=microsoft/BioGPT-Large
LLM_MAX_TOKENS=512
```

---

### Step 6: Start the System

```bash
# Start backend server
python scripts/run.py

# In another terminal, start frontend
cd frontend
python -m http.server 3000
```

**Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📊 Data Source Comparison

| Source | Size | Coverage | Cost | Setup Time | Recommended For |
|--------|------|----------|------|------------|-----------------|
| **MedQuAD** | ~50MB | 5K QA pairs | Free | 10 min | ✓ Quick start, testing |
| **Disease Ontology** | ~50MB | 10K diseases | Free | 10 min | ✓ Disease relationships |
| **UMLS (subset)** | ~2-5GB | 200K concepts | Free* | 2 hours | ✓ Medical terminology |
| **UMLS (full)** | ~30GB | 4M+ concepts | Free* | 1 day | ✓ Comprehensive system |
| **PubMed API** | ~0 | 7M+ articles | Free | 1 hour | ✓ Real-time research |
| **PubMed Embeddings** | ~100GB | 7M+ articles | Free | 1 week | ✓ Offline, fast retrieval |

*Requires free NIH license

---

## 🎯 Recommended Configurations

### Configuration 1: Development (Minimal)
**Use for**: Testing, development, prototyping

```bash
Data Sources:
✓ MedQuAD (5K QA pairs)
✓ Disease Ontology
✗ UMLS
✗ PubMed embeddings

Infrastructure:
✓ ChromaDB (vector store)
✓ NetworkX (in-memory KG)
✗ Neo4j

Size: ~500MB
Setup time: 30 minutes
```

### Configuration 2: Production (Balanced)
**Use for**: Production deployments, medium scale

```bash
Data Sources:
✓ MedQuAD (5K QA pairs)
✓ Disease Ontology
✓ UMLS subset (SNOMED + RxNorm)
✓ PubMed API (real-time)

Infrastructure:
✓ ChromaDB (vector store)
✓ Neo4j (persistent KG)
✗ Prebuilt PubMed embeddings

Size: ~3-5GB
Setup time: 3-4 hours
```

### Configuration 3: Enterprise (Comprehensive)
**Use for**: Large-scale production, research institutions

```bash
Data Sources:
✓ MedQuAD (5K QA pairs)
✓ UMLS full (4M+ concepts)
✓ PubMed embeddings (7M+ articles)

Infrastructure:
✓ ChromaDB (vector store)
✓ Neo4j cluster (distributed KG)
✓ Redis (caching)

Size: ~150GB+
Setup time: 1-2 days
Requires: 200GB+ disk, 32GB+ RAM
```

---

## 🔧 Troubleshooting

### UMLS API Issues

**Problem**: "Authentication failed"
```bash
# Solution: Verify API key
python -c "import os; print(os.getenv('UMLS_API_KEY'))"

# Get new API key from: https://uts.nlm.nih.gov/uts/profile
```

**Problem**: "Rate limit exceeded"
```bash
# Solution: Add delays between requests (built into scripts)
# Or download full UMLS and use local files
```

### Neo4j Connection Issues

**Problem**: "Connection refused"
```bash
# Solution: Verify Neo4j is running
# Windows: Check Services for Neo4j
# Or check Docker: docker ps | grep neo4j

# Test connection:
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); driver.verify_connectivity(); print('✓ Connected')"
```

**Problem**: "Authentication failed"
```bash
# Solution: Reset Neo4j password
# Access http://localhost:7474 and change password
# Update .env with new password
```

### PubMed API Issues

**Problem**: "Email required"
```bash
# Solution: Always provide email for NCBI
$env:PUBMED_EMAIL="your.email@example.com"
```

**Problem**: "Slow downloads"
```bash
# Solution: Get NCBI API key for 10x faster rate limit
# Register at: https://www.ncbi.nlm.nih.gov/account/
```

---

## 📚 Additional Resources

- **UMLS Documentation**: https://www.nlm.nih.gov/research/umls/
- **PubMed E-utilities**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **Neo4j Documentation**: https://neo4j.com/docs/
- **BioBERT Paper**: https://arxiv.org/abs/1901.08746
- **ChromaDB Docs**: https://docs.trychroma.com/

---

## 🆘 Support

For issues or questions:
1. Check this documentation
2. Review TROUBLESHOOTING.md
3. Check system logs in `logs/` directory
4. Open GitHub issue with error details

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
# 1. Check data files exist
ls data/medquad_processed.json
ls data/disease_ontology_processed.json

# 2. Check vector store
python -c "from backend.retrievers import get_vector_retriever; vr = get_vector_retriever(); print(vr.get_collection_stats())"

# 3. Check knowledge graph
python -c "from backend.retrievers import get_kg_retriever; kg = get_kg_retriever(); print(f'{len(kg.graph.nodes)} nodes')"

# 4. Test API
curl http://localhost:8000/api/health

# 5. Test query
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is diabetes?", "mode": "patient"}'
```

If all checks pass: ✓ **Enterprise setup complete!**
