# Knowledge Graph Information

## 🗂️ Current Knowledge Graph Setup

### **Active Backend: NetworkX (In-Memory)**

Your system is currently using **NetworkX** as the knowledge graph backend.

---

## 📊 Knowledge Graph Comparison

| Feature | NetworkX (Current) | Neo4j (Enterprise) |
|---------|-------------------|-------------------|
| **Type** | In-memory graph | Persistent graph database |
| **Storage** | RAM only | Disk-based with cache |
| **Installation** | ✅ Built-in (Python) | ⚠️ Requires separate install |
| **Setup** | Automatic | Manual configuration |
| **Size Limit** | ~100K nodes (RAM dependent) | Billions of nodes |
| **Performance** | Fast for small graphs | Fast for all sizes |
| **Persistence** | ❌ Lost on restart | ✅ Survives restarts |
| **Query Language** | Python NetworkX API | Cypher (graph query language) |
| **Visualization** | Limited | Built-in browser UI |
| **Suitable For** | Development, <100K nodes | Production, large scale |

---

## 🔧 Current Configuration

### NetworkX (Active)

**Location**: [`backend/retrievers/kg_retriever.py`](file://c:\Users\eahkf\AppData\Roaming\Qoder\User\globalStorage\alefragnani.project-manager\medical-rag-qa\backend\retrievers\kg_retriever.py)

**Initialization**:
```python
def __init__(self, use_neo4j: bool = False):  # Default: False = NetworkX
    self.use_neo4j = use_neo4j
    self.graph = None
    self.neo4j_driver = None
    
    if use_neo4j:
        self._init_neo4j()
    else:
        self._init_networkx()  # ← Currently active
```

**Current Data**:
```python
# Sample knowledge (when no real data loaded)
Nodes: 9 entities
  - Drugs: Metformin, Amoxicillin, Doxycycline
  - Diseases: Diabetes, Sinusitis, Type2Diabetes
  - Symptoms: Nausea, Diarrhea, Headache

Edges: 7 relationships
  - Metformin → Type2Diabetes (TREATS)
  - Metformin → Nausea (CAUSES)
  - Amoxicillin → Sinusitis (TREATS)
  - etc.
```

**After `build_knowledge_graph.py` runs**:
```python
Nodes: ~1,000 diseases from Disease Ontology
Edges: ~3,000-5,000 relationships
  - IS_A (disease hierarchy)
  - SYNONYM (alternative names)
  - DEFINITION (disease descriptions)
```

---

## 📈 Data Sources for Knowledge Graph

### Current Setup (NetworkX)

1. **Disease Ontology** (Primary source after build)
   - 14,460 total diseases available
   - Using first 1,000 for performance
   - Relationships: IS_A, SYNONYM, DEFINITION

2. **Sample Medical Knowledge** (Fallback)
   - 9 nodes, 7 edges
   - Drug-disease-symptom relationships
   - Used if Disease Ontology not available

### Enterprise Setup (Optional Neo4j)

If you enable Neo4j, can add:
1. **Full Disease Ontology** (all 14,460 diseases)
2. **UMLS Knowledge Graph** (4M+ medical concepts)
3. **Custom medical relationships**
4. **Drug databases** (RxNorm)
5. **Clinical guidelines**

---

## 🔍 How Knowledge Graph is Used

### In the RAG Pipeline:

```
User Question
    ↓
Query Processing (extract entities)
    ↓
Agent Controller (decides strategy)
    ↓
┌─────────────────────────────────┐
│  Knowledge Graph Retrieval      │
│  (NetworkX or Neo4j)            │
│                                 │
│  1. Find entities in graph      │
│  2. Get related nodes/edges     │
│  3. Return as evidence          │
└─────────────────────────────────┘
    ↓
Fuse with vector search results
    ↓
Generate answer
```

### Example Query Flow:

**Question**: "What treats diabetes?"

1. **Entity Extraction**: "diabetes" → DISEASE
2. **KG Query** (NetworkX):
   ```python
   # Find "diabetes" or "Diabetes" node
   matching_nodes = [node for node in graph.nodes() 
                     if "diabetes" in str(node).lower()]
   
   # Get incoming edges (what treats it)
   in_edges = graph.in_edges("Type2Diabetes", data=True)
   # Result: Metformin TREATS Type2Diabetes
   ```
3. **Evidence**: "Metformin TREATS Type2Diabetes"
4. **Combined with vector search** for comprehensive answer

---

## ⚙️ Switching to Neo4j (Optional)

### When to Use Neo4j:

- ✅ Need **persistent storage** (survives restarts)
- ✅ Working with **large graphs** (>100K nodes)
- ✅ Need **complex graph queries** (multi-hop relationships)
- ✅ Want **graph visualization**
- ✅ Building **production system**

### How to Enable Neo4j:

#### Step 1: Install Neo4j

**Option A: Neo4j Desktop** (Recommended for development)
```bash
# Download from: https://neo4j.com/download/
# Install and create a database
# Default: localhost:7687, user: neo4j, password: neo4j
```

**Option B: Docker**
```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**Option C: Cloud** (Neo4j Aura)
```bash
# Sign up at: https://neo4j.com/cloud/aura/
# Get connection URI and credentials
```

#### Step 2: Configure Connection

Edit `.env` file:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

#### Step 3: Install Python Driver

```bash
pip install neo4j
```

#### Step 4: Modify Initialization

**Option A**: Change default in `kg_retriever.py`:
```python
def __init__(self, use_neo4j: bool = True):  # Changed from False
```

**Option B**: Pass parameter when creating:
```python
kg_retriever = KnowledgeGraphRetriever(use_neo4j=True)
```

#### Step 5: Rebuild Knowledge Graph

```bash
python scripts/build_knowledge_graph.py
```

The system will automatically:
1. Try to connect to Neo4j
2. If successful, use Neo4j
3. If failed, fall back to NetworkX

---

## 💾 Storage Comparison

### NetworkX (Current)
```
Memory Usage: ~100MB (for 1,000 nodes)
Disk Usage: 0 bytes (in-memory only)
Persistence: ❌ Lost on restart
Loading Time: <1 second
```

### Neo4j
```
Memory Usage: ~500MB-2GB (cache)
Disk Usage: ~1-5GB (database files)
Persistence: ✅ Saved to disk
Loading Time: 2-5 seconds (from disk)
```

---

## 📊 Performance Comparison

### Query Speed (for medical questions):

| Graph Size | NetworkX | Neo4j |
|------------|----------|-------|
| 1K nodes | 10ms ⚡ | 5ms ⚡⚡ |
| 10K nodes | 50ms ⚡ | 8ms ⚡⚡ |
| 100K nodes | 500ms ⚠️ | 12ms ⚡⚡ |
| 1M+ nodes | ❌ Out of memory | 20ms ⚡⚡ |

**Recommendation**:
- **NetworkX**: Perfect for <10K nodes (your current setup with 1K diseases)
- **Neo4j**: Better for >10K nodes or if you need persistence

---

## 🔄 Data Flow with Disease Ontology

### When `build_knowledge_graph.py` Runs:

```python
# Load Disease Ontology (14,460 diseases)
diseases = load_disease_ontology_processed()

# Extract first 1,000 for NetworkX
for disease in diseases[:1000]:
    # Add node
    kg.add_knowledge(
        subject=disease['name'],
        predicate="DEFINITION",
        object=disease['definition']
    )
    
    # Add relationships
    for rel in disease['relationships']:
        kg.add_knowledge(
            subject=disease['name'],
            predicate="IS_A",
            object=rel['target']
        )
    
    # Add synonyms
    for synonym in disease['synonyms']:
        kg.add_knowledge(
            subject=disease['name'],
            predicate="SYNONYM",
            object=synonym
        )
```

**Result** (NetworkX):
```
Nodes: ~1,000 diseases
Edges: ~3,000-5,000 relationships
Types: DEFINITION, IS_A, SYNONYM
```

---

## 🎯 Current System Architecture

```
┌─────────────────────────────────────────┐
│         User Question                    │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│     Query Processor                      │
│  • Extract entities                      │
│  • Detect mode (DOCTOR/PATIENT)         │
│  • Suggest strategy                      │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│     Agent Controller                     │
│  • Decide: KG, Vector, or Hybrid        │
└──────────────┬───────────────────────────┘
               ↓
      ┌────────┴────────┐
      ↓                  ↓
┌─────────────┐  ┌──────────────────┐
│   Vector    │  │  Knowledge Graph │
│   Store     │  │   (NetworkX)     │  ← YOU ARE HERE
│             │  │                  │
│ BioBERT     │  │  Disease        │
│ ChromaDB    │  │  Ontology       │
│ 16,410 docs │  │  1,000 nodes    │
└─────────────┘  └──────────────────┘
      ↓                  ↓
      └────────┬─────────┘
               ↓
┌──────────────────────────────────────────┐
│     Evidence Fusion                      │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│     Answer Generation (BioGPT)          │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│     Safety Validation                    │
└──────────────┬───────────────────────────┘
               ↓
         Final Answer
```

---

## ✅ Summary

**Current KG**: NetworkX (in-memory)  
**Data Source**: Disease Ontology (14,460 diseases available)  
**Active Nodes**: Will be ~1,000 after build  
**Active Edges**: Will be ~3,000-5,000 after build  
**Storage**: RAM only (no persistence)  
**Performance**: Excellent for current scale  
**Status**: ✅ Ready to use (will populate when build_knowledge_graph.py runs)

**To Upgrade to Neo4j**:
1. Install Neo4j
2. Configure `.env` 
3. Run `pip install neo4j`
4. Change `use_neo4j=True` in initialization
5. Rebuild knowledge graph

---

## 🆘 Troubleshooting

**Q: How do I check which KG is active?**
```python
from backend.retrievers import get_kg_retriever

kg = get_kg_retriever()
print(f"Using Neo4j: {kg.use_neo4j}")
print(f"Nodes: {len(kg.graph.nodes) if kg.graph else 0}")
print(f"Edges: {len(kg.graph.edges) if kg.graph else 0}")
```

**Q: Can I use both NetworkX and Neo4j?**
No - the system uses one backend at a time. But you can switch between them.

**Q: Will I lose data switching to Neo4j?**
No - you just rebuild the knowledge graph from Disease Ontology.

**Q: Is NetworkX sufficient for production?**
Yes, for graphs <100K nodes. Your current 1K nodes is well within limits.

---

Your system uses **NetworkX** - perfect for your current needs! 🎉
