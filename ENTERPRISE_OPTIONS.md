# Enterprise Configuration Options

## 🎯 You Have 3 Setup Paths Available

---

## Path 1: Use What's Already Downloaded (Recommended for 18GB disk)

**Status**: MedQuAD already downloaded ✓

### What you have:
- ✓ MedQuAD dataset (~5,000 medical QA pairs from NIH, CDC, Mayo Clinic)
- ✓ Located in: `data/MedQuAD-master/`
- ✓ Categories: Cancer, GARD, GHR, CDC, NINDS, etc.

### Next steps:
```bash
# 1. Process the downloaded data
python scripts/download_real_data.py

# 2. Build vector store (will use MedQuAD + Disease Ontology)
python scripts/build_vector_store.py

# 3. Build knowledge graph (will use Disease Ontology)
python scripts/build_knowledge_graph.py

# 4. Start system
python scripts/run.py
```

**Disk usage**: ~2GB total  
**Setup time**: 30-60 minutes  
**Quality**: Production-ready for most use cases

---

## Path 2: Add UMLS Knowledge Graph (Enterprise Medical Terminology)

### What it adds:
- 4 million+ medical concepts
- 200+ medical vocabularies (SNOMED CT, RxNorm, ICD-10, etc.)
- Standardized medical terminology
- Comprehensive disease/drug relationships

### Requirements:
1. **Free UMLS License**:
   - Sign up: https://uts.nlm.nih.gov/uts/signup-login
   - Accept license agreement
   - Get API key from profile

2. **Choose subset to save disk space**:
   - **Essential** (~2GB): Core medical concepts only
   - **SNOMED + RxNorm** (~5GB): Diseases + Drugs (recommended)
   - **Full UMLS** (~30GB): Everything (requires more disk space)

### Setup:
```bash
# Set your UMLS API key
$env:UMLS_API_KEY="your-api-key-here"

# Download UMLS concepts
python scripts/download_umls.py

# Then proceed with vector store and KG build
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py
```

**Disk usage**: +2-30GB (depending on subset)  
**Setup time**: +2-4 hours  
**Benefits**: Better medical terminology coverage, standardized concepts

---

## Path 3: Add PubMed Literature (Evidence-Based Research)

### What it adds:
- Access to 7+ million peer-reviewed medical articles
- Real-time or prebuilt embeddings
- Evidence-based answers from research

### Two options:

#### Option A: API Mode (Recommended for limited disk space)
```bash
# Set your email (required)
$env:PUBMED_EMAIL="your.email@example.com"

# Optional: API key for faster downloads
$env:PUBMED_API_KEY="your-ncbi-api-key"

# Download articles
python scripts/download_pubmed.py
```

**Disk usage**: ~50MB (500 articles)  
**Setup time**: 30-60 minutes  
**Benefits**: On-demand access, no large downloads

#### Option B: Prebuilt Embeddings (For high-performance systems)
- Full embeddings: ~100GB
- Subset (top journals): ~20GB
- ⚠️ **Not recommended for 18GB available disk space**

---

## Path 4: Add Neo4j Persistent Storage (Scalable Graph Database)

### What it adds:
- Persistent graph storage (survives restarts)
- Fast graph traversal queries
- Scalable to millions of nodes
- Graph visualization

### Requirements:
1. **Install Neo4j**:
   - Download: https://neo4j.com/download/
   - OR Docker: `docker run -p 7474:7474 -p 7687:7687 neo4j`

2. **Configure connection**:
   ```bash
   # Edit .env file
   NEO4J_ENABLED=true
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. **Install Python driver**:
   ```bash
   pip install neo4j
   ```

**Disk usage**: ~1-5GB (in Neo4j database)  
**Setup time**: 30 minutes (if Neo4j already installed)  
**Benefits**: Persistent storage, better performance for complex queries

---

## 🎯 Recommended Configuration for Your System (18GB disk)

Given your **18GB available disk space**, here's the optimal setup:

### ✓ Recommended: Path 1 + Path 2 (Essential) + Path 3 (API)

```bash
# 1. Use already-downloaded MedQuAD ✓
python scripts/download_real_data.py

# 2. Add UMLS Essential subset (optional, +2GB)
$env:UMLS_API_KEY="your-key"
python scripts/download_umls.py
# Choose "Essential Medical (~2GB)" when prompted

# 3. Add PubMed API access (optional, minimal disk)
$env:PUBMED_EMAIL="your.email@example.com"
python scripts/download_pubmed.py

# 4. Build everything
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py

# 5. Start system
python scripts/run.py
```

**Total disk usage**: ~4-5GB  
**Quality**: Enterprise-grade  
**Benefits**: Real medical data, standardized terminology, research literature

---

## 📊 Quick Comparison

| Component | Disk | Time | Quality | Recommended? |
|-----------|------|------|---------|--------------|
| MedQuAD (already downloaded) | ~1GB | ✓ Done | ⭐⭐⭐⭐ | ✅ Yes |
| Disease Ontology | ~50MB | 10 min | ⭐⭐⭐⭐ | ✅ Yes |
| UMLS Essential | ~2GB | 2 hours | ⭐⭐⭐⭐⭐ | ✅ Yes (if you have API key) |
| UMLS SNOMED+RxNorm | ~5GB | 2 hours | ⭐⭐⭐⭐⭐ | ⚠️ Maybe (disk space tight) |
| UMLS Full | ~30GB | 1 day | ⭐⭐⭐⭐⭐ | ❌ No (insufficient disk) |
| PubMed API | ~50MB | 1 hour | ⭐⭐⭐⭐ | ✅ Yes |
| PubMed Embeddings | ~100GB | 1 week | ⭐⭐⭐⭐⭐ | ❌ No (insufficient disk) |
| Neo4j | ~1-5GB | 30 min | ⭐⭐⭐⭐⭐ | ⚠️ Optional |

---

## 🚀 Quickest Path to Production

If you want to get started **right now** with what you have:

```bash
# Just use the already-downloaded MedQuAD data
cd medical-rag-qa

# Process it
python scripts/download_real_data.py

# Build stores (will auto-detect MedQuAD)
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py

# Start
python scripts/run.py
```

**Time**: 30 minutes  
**Quality**: Production-ready  
**Disk**: ~2GB total

Then you can add UMLS/PubMed/Neo4j later if needed!

---

## 📝 Current Interactive Setup

The `enterprise_setup.py` wizard is currently waiting for your input. It will:
1. Ask if you have UMLS API key
2. Ask if you have Neo4j installed
3. Ask which PubMed option you want
4. Generate .env configuration automatically

You can:
- **Continue with wizard** (press Enter in terminal)
- **OR skip wizard** and follow manual steps above
- **OR use quickest path** (recommended to start)

---

## ❓ Decision Helper

**Q: I just want it working quickly**  
A: Use "Quickest Path" above with MedQuAD only

**Q: I want best quality answers**  
A: Add UMLS (essential subset) + PubMed API

**Q: I have UMLS API key already**  
A: Definitely add UMLS, it's worth it!

**Q: I don't have UMLS license yet**  
A: Still works great with MedQuAD + Disease Ontology. Get UMLS later.

**Q: Should I use Neo4j?**  
A: Optional. NetworkX works fine for <100K nodes. Neo4j is better for larger scale.

**Q: What about the disk space warning?**  
A: You have enough for MedQuAD + UMLS Essential + PubMed API (~4-5GB total)
