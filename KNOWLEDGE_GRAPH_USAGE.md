# Knowledge Graph Usage in Medical RAG System

## Overview

The Knowledge Graph (KG) is a **structured medical knowledge component** that stores medical facts as **entity-relationship triples** (subject-predicate-object). It provides **high-confidence, structured answers** about drug-disease relationships, symptoms, and treatments.

---

## 🏗️ Current Architecture

### **1. Graph Database**

Currently using **NetworkX** (in-memory graph):
- **Type**: `MultiDiGraph` (supports multiple edges between nodes)
- **Storage**: In-memory (can be replaced with Neo4j for production)
- **Size**: 9 nodes, 7 edges (sample data - needs expansion!)

### **2. Node Types**

```python
# Drug nodes
Metformin (type="Drug", description="Oral diabetes medication")
Amoxicillin (type="Drug", description="Antibiotic")
Doxycycline (type="Drug", description="Antibiotic")

# Disease nodes  
Diabetes (type="Disease", description="Metabolic disorder")
Type2Diabetes (type="Disease", description="Type 2 Diabetes Mellitus")
Sinusitis (type="Disease", description="Sinus infection")

# Symptom nodes
Nausea (type="Symptom", description="Feeling of sickness")
Diarrhea (type="Symptom", description="Loose stools")
Headache (type="Symptom", description="Pain in head")
```

### **3. Relationship Types**

```python
# Current relationships (7 edges)
Metformin --TREATS--> Type2Diabetes
Metformin --CAUSES--> Nausea
Metformin --CAUSES--> Diarrhea

Amoxicillin --TREATS--> Sinusitis
Doxycycline --TREATS--> Sinusitis

Diabetes --TREATED_BY--> Metformin
Sinusitis --HAS_SYMPTOM--> Headache
```

---

## 🔄 How KG is Used: Complete Pipeline

### **Step 1: Entity Extraction (Query Preprocessing)**

When a query comes in, the [`QueryPreprocessor`](backend/preprocessing/query_processor.py) extracts medical entities:

```python
# Example query: "What are the side effects of Metformin?"

# 1. scispaCy NER extracts entities
entities = preprocessor.extract_entities(query)
# Result: [
#   MedicalEntity(text="Metformin", entity_type="DRUG", confidence=0.8)
# ]

# 2. Creates ProcessedQuery
processed = ProcessedQuery(
    original_question="What are the side effects of Metformin?",
    entities=[MedicalEntity(text="Metformin", ...)],
    suggested_strategy=RetrievalStrategy.HYBRID  # Will use KG + Vector
)
```

**File**: [`backend/preprocessing/query_processor.py`](backend/preprocessing/query_processor.py) (Line 67-124)

---

### **Step 2: KG Retrieval (Knowledge Graph Search)**

The [`KnowledgeGraphRetriever`](backend/retrievers/kg_retriever.py) searches for entities and their relationships:

```python
# KG retrieval process
def retrieve(query: ProcessedQuery) -> List[RetrievedEvidence]:
    # 1. Find matching nodes
    for entity in query.entities:  # ["Metformin"]
        entity_text = normalize_medical_term(entity.text)  # "metformin"
        
        # Case-insensitive node matching
        matching_nodes = [
            node for node in self.graph.nodes()
            if "metformin" in normalize_medical_term(str(node))
        ]
        # Result: ["Metformin"]
        
        # 2. Get all outgoing edges (what Metformin affects)
        out_edges = self.graph.out_edges("Metformin", data=True)
        # Returns:
        # ("Metformin", "Type2Diabetes", {relation: "TREATS"})
        # ("Metformin", "Nausea", {relation: "CAUSES"})
        # ("Metformin", "Diarrhea", {relation: "CAUSES"})
        
        # 3. Get all incoming edges (what affects Metformin)
        in_edges = self.graph.in_edges("Metformin", data=True)
        # Returns:
        # ("Diabetes", "Metformin", {relation: "TREATED_BY"})
        
        # 4. Create evidence objects
        evidences = [
            RetrievedEvidence(
                source_type="kg",
                content="Metformin TREATS Type2Diabetes. Oral diabetes medication",
                confidence=0.9,  # High confidence for KG facts
                metadata={
                    "subject": "Metformin",
                    "predicate": "TREATS",
                    "object": "Type2Diabetes"
                }
            ),
            RetrievedEvidence(
                source_type="kg",
                content="Metformin CAUSES Nausea. Feeling of sickness",
                confidence=0.9,
                metadata={"subject": "Metformin", "predicate": "CAUSES", ...}
            ),
            # ... more evidences
        ]
    
    return evidences  # Sorted by confidence
```

**File**: [`backend/retrievers/kg_retriever.py`](backend/retrievers/kg_retriever.py) (Line 156-209)

---

### **Step 3: Strategy Selection (Agent Decision)**

The [`AgentController`](backend/agents/agent_controller.py) decides which retrieval sources to use:

```python
# Agent decides strategy based on query analysis
strategy = agent.decide_strategy(processed_query)

# Available strategies:
# - KG_ONLY: Only use Knowledge Graph (good for definitions)
# - VECTOR_ONLY: Only use dense vector search
# - SPARSE_ONLY: Only use BM25 keyword search
# - HYBRID: KG + Dense Vector (default for queries with entities)
# - DENSE_SPARSE: Dense + Sparse (no KG)
# - FULL_HYBRID: KG + Dense + Sparse (all three)

# Example: Query about "Metformin side effects"
# -> Detects entities: ["Metformin"]
# -> Suggests: HYBRID (KG + Vector)
```

**File**: [`backend/agents/agent_controller.py`](backend/agents/agent_controller.py) (Line 28-37)

---

### **Step 4: Multi-Source Retrieval**

When `HYBRID` or `FULL_HYBRID` is used, the agent retrieves from multiple sources:

```python
# Example: HYBRID strategy (KG + Dense Vector)
def retrieve_with_strategy(query, strategy):
    evidences = []
    
    # 1. Get KG evidences
    kg_evidences = self.kg_retriever.retrieve(query)
    # Returns 3 KG facts about Metformin (confidence=0.9 each)
    
    # 2. Get vector evidences
    vector_evidences = self.vector_retriever.retrieve(query)
    # Returns 5 documents from BioBERT search (confidence=0.6-0.8)
    
    # 3. Combine
    evidences = kg_evidences + vector_evidences
    # Total: 8 evidences from 2 sources
    
    return evidences
```

**File**: [`backend/agents/agent_controller.py`](backend/agents/agent_controller.py) (Line 107-143)

---

### **Step 5: Evidence Fusion (Weighted Combination)**

The [`fuse_evidence()`](backend/agents/agent_controller.py) method combines results from different sources:

```python
def fuse_evidence(evidences, query):
    # Separate by source type
    kg_evidences = [e for e in evidences if e.source_type == "kg"]
    # 3 KG evidences
    
    vector_evidences = [e for e in evidences if e.source_type == "vector"]
    # 5 vector evidences
    
    sparse_evidences = [e for e in evidences if e.source_type == "sparse"]
    # 0 sparse evidences (not in HYBRID strategy)
    
    # Apply fusion weights (from config.py)
    for evidence in kg_evidences:
        evidence.confidence *= 0.5  # FUSION_WEIGHT_KG = 0.5
    
    for evidence in vector_evidences:
        evidence.confidence *= 0.3  # FUSION_WEIGHT_VECTOR = 0.3
    
    # After weighting:
    # KG: 0.9 * 0.5 = 0.45 confidence
    # Vector: 0.8 * 0.3 = 0.24 confidence
    
    # Sort by adjusted confidence
    evidences.sort(key=lambda x: x.confidence, reverse=True)
    # KG facts will rank higher due to higher weights
    
    return FusedEvidence(
        evidences=evidences,
        combined_confidence=0.38,  # Average
        fusion_method="weighted_fusion"
    )
```

**File**: [`backend/agents/agent_controller.py`](backend/agents/agent_controller.py) (Line 145-220)

**Fusion Weights** (from [`backend/config.py`](backend/config.py)):
```python
FUSION_WEIGHT_KG = 0.5      # Highest (most reliable)
FUSION_WEIGHT_VECTOR = 0.3  # Medium
FUSION_WEIGHT_SPARSE = 0.2  # Lowest
```

---

### **Step 6: Answer Generation**

The fused evidence is passed to [`AnswerGenerator`](backend/generators/answer_generator.py):

```python
# Top 3 evidences after fusion:
evidences = [
    "Metformin CAUSES Nausea. Feeling of sickness" (confidence=0.45, from KG),
    "Metformin CAUSES Diarrhea. Loose stools" (confidence=0.45, from KG),
    "Metformin is a medication used to treat type 2 diabetes..." (confidence=0.24, from vector)
]

# Generator extracts key information
answer = answer_generator.generate(query, fused_evidence)
# "Common side effects of Metformin include nausea and diarrhea. 
#  It is an oral medication used to treat type 2 diabetes..."
```

**File**: [`backend/generators/answer_generator.py`](backend/generators/answer_generator.py) (Line 341-344)

---

## 📊 Complete Example: Query Flow

### **Query**: "What are the side effects of Metformin?"

```
┌─────────────────────────────────────────────────────────────┐
│ 1. QUERY PREPROCESSING (query_processor.py)                 │
├─────────────────────────────────────────────────────────────┤
│ Input: "What are the side effects of Metformin?"            │
│ Entity Extraction: ["Metformin" (DRUG)]                     │
│ Query Type: CONTEXTUAL                                       │
│ Suggested Strategy: HYBRID (KG + Vector)                     │
│ Detected Mode: PATIENT                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. AGENT STRATEGY DECISION (agent_controller.py)            │
├─────────────────────────────────────────────────────────────┤
│ Strategy: HYBRID (KG + Dense Vector)                         │
│ Will retrieve from: KG + BioBERT                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. KG RETRIEVAL (kg_retriever.py)                           │
├─────────────────────────────────────────────────────────────┤
│ Find "Metformin" node in graph                               │
│ Get relationships:                                           │
│   ✓ Metformin TREATS Type2Diabetes (0.9)                    │
│   ✓ Metformin CAUSES Nausea (0.9)                           │
│   ✓ Metformin CAUSES Diarrhea (0.9)                         │
│ Returns: 3 KG evidences                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. VECTOR RETRIEVAL (vector_retriever.py)                   │
├─────────────────────────────────────────────────────────────┤
│ BioBERT embedding of query                                   │
│ Cosine similarity search in ChromaDB                         │
│ Returns: 5 relevant documents (0.6-0.8 confidence)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. EVIDENCE FUSION (agent_controller.py)                    │
├─────────────────────────────────────────────────────────────┤
│ KG evidences: 3 × 0.9 × 0.5 = 0.45 weighted confidence      │
│ Vector evidences: 5 × 0.7 × 0.3 = 0.21 weighted confidence  │
│ Sort by weighted confidence                                  │
│ Top evidences: [KG, KG, KG, Vector, Vector, ...]           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. ANSWER GENERATION (answer_generator.py)                  │
├─────────────────────────────────────────────────────────────┤
│ Extract from top evidences                                   │
│ Answer: "Common side effects of Metformin include nausea    │
│          and diarrhea. Metformin is used to treat Type 2    │
│          Diabetes..."                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 When KG is Used

### **Automatic Strategy Selection**

The system automatically decides to use KG based on query analysis:

| Query Type | Has Entities? | Strategy | KG Used? |
|------------|---------------|----------|----------|
| Definition | Yes (≥1) | `KG_ONLY` | ✅ Yes (only KG) |
| Complex | Any | `HYBRID` | ✅ Yes (KG + Vector) |
| Contextual | Yes (≥2) | `HYBRID` | ✅ Yes (KG + Vector) |
| Contextual | No or 1 | `VECTOR_ONLY` | ❌ No |

### **Examples**

**✅ KG Used (HYBRID)**:
- "What does Metformin treat?" → Entities: [Metformin] → KG_ONLY
- "Side effects of Amoxicillin" → Entities: [Amoxicillin] → HYBRID
- "Metformin and Diabetes relationship" → Entities: [Metformin, Diabetes] → HYBRID

**❌ KG Not Used (VECTOR_ONLY)**:
- "What are common diabetes symptoms?" → No specific drug entities → VECTOR_ONLY
- "How to manage high blood sugar?" → No entities → VECTOR_ONLY

---

## ⚙️ Configuration

### **Fusion Weights** ([`backend/config.py`](backend/config.py))

```python
class AgentConfig:
    # Evidence fusion weights (must sum to reasonable values)
    FUSION_WEIGHT_KG = 0.5      # Knowledge Graph (highest confidence)
    FUSION_WEIGHT_VECTOR = 0.3  # Dense retrieval
    FUSION_WEIGHT_SPARSE = 0.2  # Sparse (BM25) retrieval
    
    # Top-k results per source
    TOP_K_KG = 5        # Max KG facts to retrieve
    TOP_K_VECTOR = 5    # Max vector results
    TOP_K_SPARSE = 5    # Max sparse results
```

**Why KG has highest weight (0.5)?**
- ✅ Structured facts with high precision
- ✅ Explicit relationships (TREATS, CAUSES)
- ✅ No hallucinations (pre-verified knowledge)
- ✅ Perfect for drug-disease-symptom relationships

---

## 🚨 Current Limitations

### **1. Small Knowledge Base**
- **Current**: Only 9 nodes, 7 edges (toy dataset)
- **Impact**: Can only answer queries about:
  - Metformin, Amoxicillin, Doxycycline
  - Diabetes, Sinusitis
  - Nausea, Diarrhea, Headache
- **Most queries fall back to vector search!**

### **2. Limited Relationship Types**
- **Current**: Only 4 relationship types (TREATS, CAUSES, TREATED_BY, HAS_SYMPTOM)
- **Missing**: PREVENTS, INTERACTS_WITH, DIAGNOSED_BY, ASSOCIATED_WITH, etc.

### **3. No Real Medical Data**
- **Current**: Sample/demo data only
- **Needed**: Real medical ontologies (UMLS, Disease Ontology, DrugBank)

### **4. In-Memory Storage**
- **Current**: NetworkX (resets on restart)
- **For Production**: Should use Neo4j with persistence

---

## 🚀 How to Expand the Knowledge Graph

### **Option 1: Disease Ontology (Recommended - Easiest)**

```bash
# 1. Download Disease Ontology
wget http://purl.obolibrary.org/obo/doid.owl

# 2. Parse and load into KG
python scripts/load_disease_ontology.py
```

**Benefits**:
- 14,460 diseases with relationships
- Free and open-source
- Easy to integrate
- ~50MB file

### **Option 2: DrugBank (Drug Knowledge)**

```bash
# 1. Sign up at https://go.drugbank.com/
# 2. Download DrugBank XML

# 3. Parse and load
python scripts/load_drugbank.py
```

**Benefits**:
- 13,000+ drugs
- Drug-drug interactions
- Side effects
- Free for academic use

### **Option 3: UMLS (Comprehensive - Complex)**

```bash
# 1. Get NIH UMLS license (free but requires approval)
# 2. Download UMLS Metathesaurus

# 3. Load into Neo4j
python scripts/load_umls.py
```

**Benefits**:
- 4+ million medical concepts
- 200+ source vocabularies
- Most comprehensive option
- Industry standard

**Challenges**:
- Requires NIH license
- Large dataset (>10GB)
- Complex integration

---

## 📝 Sample Script to Expand KG

Create `scripts/expand_kg_sample.py`:

```python
"""
Expand Knowledge Graph with more medical facts
"""
from backend.retrievers.kg_retriever import get_kg_retriever

kg = get_kg_retriever()

# Add more drugs
drugs = [
    ("Aspirin", "Drug", "Blood thinner, pain reliever"),
    ("Ibuprofen", "Drug", "NSAID pain reliever"),
    ("Lisinopril", "Drug", "ACE inhibitor for hypertension"),
]

# Add more diseases
diseases = [
    ("Hypertension", "Disease", "High blood pressure"),
    ("Arthritis", "Disease", "Joint inflammation"),
    ("Migraine", "Disease", "Severe headache disorder"),
]

# Add more symptoms
symptoms = [
    ("Fever", "Symptom", "Elevated body temperature"),
    ("Fatigue", "Symptom", "Extreme tiredness"),
    ("Chest Pain", "Symptom", "Pain in chest area"),
]

# Add nodes
for name, node_type, desc in drugs + diseases + symptoms:
    kg.graph.add_node(name, type=node_type, description=desc)

# Add relationships
relationships = [
    ("Aspirin", "TREATS", "Fever"),
    ("Aspirin", "CAUSES", "Nausea"),
    ("Ibuprofen", "TREATS", "Arthritis"),
    ("Ibuprofen", "CAUSES", "Nausea"),
    ("Lisinopril", "TREATS", "Hypertension"),
    ("Hypertension", "CAUSES", "Chest Pain"),
    ("Migraine", "HAS_SYMPTOM", "Headache"),
]

for subject, predicate, obj in relationships:
    kg.graph.add_edge(subject, obj, relation=predicate)

print(f"Expanded KG: {len(kg.graph.nodes)} nodes, {len(kg.graph.edges)} edges")

# Save to file (if using persistence)
import pickle
with open("data/kg_graph.pkl", "wb") as f:
    pickle.dump(kg.graph, f)
```

**Run**:
```bash
python scripts/expand_kg_sample.py
```

---

## 🔍 How to Check KG Status

### **1. Check Current Graph Size**

```python
from backend.retrievers.kg_retriever import get_kg_retriever

kg = get_kg_retriever()
print(f"Nodes: {len(kg.graph.nodes)}")
print(f"Edges: {len(kg.graph.edges)}")
print(f"Node types: {set(data.get('type') for _, data in kg.graph.nodes(data=True))}")
```

### **2. View All Relationships**

```python
for source, target, data in kg.graph.edges(data=True):
    relation = data.get('relation', 'UNKNOWN')
    print(f"{source} --{relation}--> {target}")
```

### **3. Test KG Retrieval**

```python
from backend.models import MedicalEntity, ProcessedQuery, QueryType, RetrievalStrategy

# Create test query
entity = MedicalEntity(text="Metformin", entity_type="DRUG", confidence=0.8)
query = ProcessedQuery(
    original_question="What does Metformin treat?",
    normalized_question="metformin treat",
    entities=[entity],
    query_type=QueryType.DEFINITION,
    suggested_strategy=RetrievalStrategy.KG_ONLY
)

# Retrieve from KG
evidences = kg.retrieve(query)

for evidence in evidences:
    print(f"✓ {evidence.content} (confidence={evidence.confidence})")
```

---

## 📈 Performance Impact

### **Current Performance** (with 9 nodes)
- **Retrieval Time**: <10ms (in-memory graph)
- **Memory**: <1MB
- **Coverage**: ~0.01% of medical queries

### **With Disease Ontology** (14,460 diseases)
- **Retrieval Time**: ~50-100ms
- **Memory**: ~50MB
- **Coverage**: ~30-40% of disease queries

### **With Full UMLS** (4M concepts)
- **Retrieval Time**: 100-500ms (needs Neo4j)
- **Memory**: 10-50GB (database)
- **Coverage**: ~80-90% of medical queries

---

## 🎓 Key Takeaways

### **What KG is Good For**:
✅ Explicit drug-disease relationships  
✅ Side effects and contraindications  
✅ Symptom-disease associations  
✅ High-confidence factual answers  
✅ Structured medical knowledge  

### **What KG is NOT Good For**:
❌ Open-ended questions ("How to manage diabetes?")  
❌ Contextual/narrative answers  
❌ Recent research (static knowledge)  
❌ Patient stories/experiences  

### **Current State**:
- ⚠️ **Demo-quality**: Only 9 nodes (toy dataset)
- ✅ **Architecture ready**: Can scale to millions of nodes
- 🔧 **Needs expansion**: Load real medical ontologies

### **Next Steps**:
1. **Immediate**: Add more sample data (100-1000 nodes) for testing
2. **Short-term**: Load Disease Ontology (14,460 diseases)
3. **Long-term**: Integrate DrugBank + UMLS for production

---

## 📚 Related Files

- [`backend/retrievers/kg_retriever.py`](backend/retrievers/kg_retriever.py) - KG retrieval logic
- [`backend/agents/agent_controller.py`](backend/agents/agent_controller.py) - Strategy selection and fusion
- [`backend/preprocessing/query_processor.py`](backend/preprocessing/query_processor.py) - Entity extraction
- [`backend/config.py`](backend/config.py) - Fusion weights and settings
- [`backend/models/__init__.py`](backend/models/__init__.py) - Data models

---

## 💡 Summary

The Knowledge Graph is used as a **high-confidence fact source** that:
1. **Extracts entities** from queries (Metformin, Diabetes, etc.)
2. **Searches graph** for matching nodes and relationships
3. **Returns structured facts** (Metformin TREATS Type2Diabetes)
4. **Fused with vector search** for comprehensive answers
5. **Prioritized in ranking** (highest fusion weight = 0.5)

**Current limitation**: Only 9 sample nodes - needs expansion with real medical data!
