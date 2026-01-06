# 🏗️ Architecture Documentation

## System Overview

The Medical RAG QA system is an **Agentic Retrieval-Augmented Generation** pipeline that combines:
- Knowledge Graphs (structured medical knowledge)
- Vector Databases (semantic document search)
- Large Language Models (answer generation)
- Safety Reflection (validation layer)

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  1. Query Preprocessing (NER + UMLS)        │
│     - Extract entities (drugs, diseases)    │
│     - Map to UMLS concepts                  │
│     - Classify query type                   │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  2. Agent Decision Layer                    │
│     - Analyze query complexity              │
│     - Choose retrieval strategy:            │
│       • KG Only (definitions)               │
│       • Vector Only (contextual)            │
│       • Hybrid (complex queries)            │
└──────┬──────────────────────────────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ KG Ret.  │  │ Vec Ret. │  │  Hybrid  │
│ Neo4j/   │  │ ChromaDB │  │ KG + Vec │
│ NetworkX │  │ + BioBERT│  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     └─────────────┼─────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. Evidence Fusion                         │
│     - Combine KG facts + documents          │
│     - Weight by confidence                  │
│     - Rank and deduplicate                  │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  4. Answer Generation (LLM)                 │
│     - BioGPT / FLAN-T5 / GPT-4              │
│     - Mode-aware prompts                    │
│     - Evidence-grounded generation          │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  5. Safety Reflection                       │
│     - Check for harmful content             │
│     - Verify evidence alignment             │
│     - Detect hallucinations                 │
│     - Add disclaimers                       │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ Final Answer│
└─────────────┘
```

---

## Component Architecture

### 1. Query Preprocessing (`backend/preprocessing/`)

**Purpose:** Understand and normalize medical queries

**Components:**
- **scispaCy NER:** Extracts medical entities (drugs, diseases, symptoms)
- **UMLS Linker:** Maps entities to standard medical concepts
- **Query Classifier:** Determines query type (definition/contextual/complex)

**Flow:**
```python
Raw Query → Entity Extraction → UMLS Mapping → Query Classification → ProcessedQuery
```

**Technologies:**
- scispaCy (medical NLP)
- UMLS Metathesaurus
- spaCy pipelines

---

### 2. Agent Controller (`backend/agents/`)

**Purpose:** Orchestrate retrieval strategy based on query analysis

**Decision Logic:**
```python
if query_type == "definition" and entities_found:
    strategy = "kg_only"
elif query_type == "complex" or multiple_entities:
    strategy = "hybrid"
else:
    strategy = "vector_only"
```

**Responsibilities:**
- Analyze processed query
- Select optimal retrieval strategy
- Coordinate retrievers
- Fuse retrieved evidence

**Technologies:**
- Custom decision logic (can be extended with LangChain ReAct)

---

### 3. Retrieval Systems

#### 3A. Vector Retriever (`backend/retrievers/vector_retriever.py`)

**Purpose:** Semantic search over medical documents

**Components:**
- **Embedding Model:** BioBERT (domain-specific BERT for biomedical text)
- **Vector Store:** ChromaDB with FAISS indexing
- **Documents:** PubMed abstracts, MedQuAD Q&A pairs

**Process:**
```python
Query → BioBERT Embedding → FAISS Search → Top-K Documents → RetrievedEvidence
```

**Configuration:**
- Embedding dimension: 768 (BioBERT)
- Similarity metric: Cosine similarity
- Top-K: Configurable (default: 5)

#### 3B. Knowledge Graph Retriever (`backend/retrievers/kg_retriever.py`)

**Purpose:** Structured knowledge lookup

**Storage Options:**
- **NetworkX:** In-memory graph (for development)
- **Neo4j:** Persistent graph database (for production)

**Graph Schema:**
```
Nodes: Drug, Disease, Symptom, Treatment
Edges: TREATS, CAUSES, HAS_SYMPTOM, RELATED_TO
```

**Query Examples:**
```cypher
// Find treatments for a disease
MATCH (d:Drug)-[:TREATS]->(disease:Disease {name: "Diabetes"})
RETURN d.name

// Find side effects of a drug
MATCH (drug:Drug {name: "Metformin"})-[:CAUSES]->(s:Symptom)
RETURN s.name
```

**Technologies:**
- NetworkX (development)
- Neo4j (production)
- UMLS data

---

### 4. Evidence Fusion

**Purpose:** Combine results from multiple retrievers

**Fusion Strategy:**
```python
# Weighted combination
kg_weight = 0.6
vector_weight = 0.4

for evidence in kg_evidences:
    evidence.confidence *= kg_weight

for evidence in vector_evidences:
    evidence.confidence *= vector_weight

combined = kg_evidences + vector_evidences
ranked = sort_by_confidence(combined)
```

**Output:** `FusedEvidence` with ranked sources

---

### 5. Answer Generation (`backend/generators/`)

**Purpose:** Generate natural language answers from evidence

**Model Options:**
1. **BioGPT** (default)
   - Specialized for biomedical text
   - Pre-trained on PubMed
   - Good for medical terminology

2. **FLAN-T5**
   - General purpose, instruction-tuned
   - Faster inference
   - Good for simple queries

3. **OpenAI GPT-4** (optional)
   - Best quality
   - Requires API key
   - Higher cost

**Prompt Engineering:**

*Patient Mode:*
```
You are a helpful medical assistant. Based on the following medical 
information, provide a clear, easy-to-understand answer.

Question: {question}
Evidence: {evidence}

Answer in simple language and include a disclaimer.
```

*Doctor Mode:*
```
You are a medical expert. Based on the evidence, provide a detailed,
technical answer with citations.

Question: {question}
Evidence: {evidence}

Use medical terminology and cite sources.
```

---

### 6. Safety Reflection (`backend/safety/`)

**Purpose:** Validate answers before returning to users

**Safety Checks:**

1. **Harmful Content Detection**
   - Specific dosage recommendations → ❌
   - "No need to see doctor" → ❌
   - "Guaranteed cure" → ❌

2. **Disclaimer Validation**
   - Patient mode MUST include healthcare consultation advice

3. **Hallucination Detection**
   - Extract medical terms from answer
   - Verify presence in evidence
   - Flag unsupported claims

4. **Evidence Alignment**
   - Compare answer content with source documents
   - Calculate overlap/faithfulness score

**Auto-Correction:**
- Remove harmful patterns
- Add missing disclaimers
- Reduce confidence if corrections applied

---

## Data Flow

### Complete Request Flow

```
1. HTTP POST /api/ask
   ↓
2. FastAPI receives MedicalQuery
   ↓
3. QueryPreprocessor extracts entities
   ↓
4. AgentController decides strategy
   ↓
5. Retrievers fetch evidence (parallel)
   ├─ VectorRetriever → ChromaDB
   └─ KGRetriever → NetworkX/Neo4j
   ↓
6. Evidence fusion and ranking
   ↓
7. AnswerGenerator creates response
   ↓
8. SafetyReflector validates
   ↓
9. Return MedicalAnswer to client
```

---

## Scalability Considerations

### Current Architecture
- Single server
- In-memory KG (NetworkX)
- Local vector store (ChromaDB)
- Suitable for: Development, small deployments

### Production Architecture

```
                    ┌─────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌────────┐       ┌────────┐       ┌────────┐
    │FastAPI │       │FastAPI │       │FastAPI │
    │Instance│       │Instance│       │Instance│
    └───┬────┘       └───┬────┘       └───┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌────────┐     ┌─────────┐     ┌─────────┐
    │ Neo4j  │     │ Vector  │     │ Redis   │
    │Cluster │     │ Store   │     │ Cache   │
    └────────┘     └─────────┘     └─────────┘
```

**Improvements:**
- Horizontal scaling with multiple FastAPI instances
- Neo4j cluster for KG
- Distributed vector store (Milvus/Pinecone)
- Redis caching for frequent queries
- GPU acceleration for LLM inference

---

## Performance Optimization

### Current Bottlenecks
1. **LLM Generation:** 2-5 seconds per query
2. **Embedding:** 100-300ms per query
3. **Vector Search:** 50-100ms
4. **KG Query:** 10-50ms

### Optimization Strategies

1. **Caching:**
```python
# Cache query embeddings
# Cache frequent query results
# TTL: 1 hour
```

2. **Batch Processing:**
```python
# Batch embed multiple queries
# Batch vector search
```

3. **Model Quantization:**
```python
# Use int8 quantized models
# 4x speedup with minimal quality loss
```

4. **Async Processing:**
```python
# Parallel retrieval from KG + Vector
# Async LLM calls
```

---

## Security Architecture

### Current (Development)
- No authentication
- No rate limiting
- HTTP only
- Local access

### Production Requirements

```
Client → HTTPS → API Gateway → Auth → Rate Limiter → FastAPI
                                                          ↓
                                                     Encryption
                                                          ↓
                                                       Database
```

**Must Implement:**
- JWT authentication
- API key management
- Rate limiting (per user/IP)
- Input sanitization
- HTTPS/TLS
- Audit logging
- Data encryption at rest

---

## Extensibility

### Adding New Retrievers

```python
class CustomRetriever:
    def retrieve(self, query: ProcessedQuery) -> List[RetrievedEvidence]:
        # Your custom retrieval logic
        pass

# Register in AgentController
agent.add_retriever("custom", CustomRetriever())
```

### Adding New LLM Models

```python
class CustomGenerator(AnswerGenerator):
    def _init_model(self):
        # Load your model
        pass
    
    def _generate(self, prompt: str) -> str:
        # Generate answer
        pass
```

### Adding New Safety Checks

```python
class CustomSafetyCheck:
    def check(self, answer: str) -> List[str]:
        # Return list of issues
        pass

reflector.add_check(CustomSafetyCheck())
```

---

## Monitoring & Observability

### Metrics to Track

1. **Performance:**
   - Request latency (p50, p95, p99)
   - Retrieval time
   - Generation time
   - Cache hit rate

2. **Quality:**
   - Average confidence scores
   - Safety validation pass rate
   - User feedback (thumbs up/down)
   - BLEU/ROUGE scores

3. **System:**
   - CPU/Memory usage
   - Database connections
   - Error rates
   - Request volume

### Logging

```python
# All logs go to logs/app.log
logger.info("Query processed", extra={
    "query_id": "...",
    "strategy": "hybrid",
    "latency_ms": 2340
})
```

---

## Future Enhancements

1. **Multi-turn Conversations**
   - Context tracking across queries
   - Follow-up question handling

2. **Advanced RAG Techniques**
   - Self-RAG (self-reflection)
   - Iterative retrieval
   - Query decomposition

3. **Medical Image Support**
   - Analyze medical images
   - Combine with text Q&A

4. **Personalization**
   - User medical history
   - Personalized recommendations

5. **Multi-lingual Support**
   - Support for multiple languages
   - Translation layer
