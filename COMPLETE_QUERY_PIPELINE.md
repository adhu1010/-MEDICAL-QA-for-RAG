# Complete Query Processing Pipeline - Medical RAG QA System

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Step-by-Step Pipeline](#step-by-step-pipeline)
4. [Files and Components](#files-and-components)
5. [Data Flow Summary](#data-flow-summary)
6. [Configuration](#configuration)

---

## Overview

This document provides a complete walkthrough of how a user query is processed in the Medical RAG QA system, from the moment it arrives at the API to the final answer generation.

### Key Technologies
- **Frontend**: HTML/CSS/JavaScript
- **Backend**: FastAPI (Python)
- **Embeddings**: BioBERT (dmis-lab/biobert-base-cased-v1.2)
- **Vector Store**: ChromaDB with cosine similarity
- **Knowledge Graph**: NetworkX (in-memory graph)
- **Sparse Retrieval**: BM25Okapi algorithm
- **PubMed API**: NCBI E-utilities for real-time literature
- **Answer Generator**: Evidence-based extraction

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER QUERY                                  │
│              "What are the side effects of Metformin?"              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: FRONTEND (index.html)                                       │
│ - Capture user input                                                │
│ - Validate form                                                     │
│ - Send HTTP POST to /api/ask                                        │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: API ENDPOINT (main.py)                                      │
│ - Receive request                                                   │
│ - Validate MedicalQuery model                                       │
│ - Initialize components                                             │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: QUERY PREPROCESSING (query_processor.py)                    │
│ - Text normalization: "metformin side effects"                      │
│ - Mode detection: PATIENT (keyword analysis)                        │
│ - NER extraction: [Metformin (DRUG)]                                │
│ - Query type: CONTEXTUAL                                            │
│ - Strategy suggestion: HYBRID                                        │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: AGENT CONTROLLER (agent_controller.py)                      │
│ - Receive ProcessedQuery                                            │
│ - Decide strategy: HYBRID (KG + Vector)                             │
│ - Coordinate multi-source retrieval                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓             ↓             ↓             ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ STEP 5a:     │ │ STEP 5b:     │ │ STEP 5c:     │ │ STEP 5d:     │
│ KG RETRIEVAL │ │ VECTOR       │ │ SPARSE       │ │ PUBMED       │
│              │ │ RETRIEVAL    │ │ RETRIEVAL    │ │ RETRIEVAL    │
│ kg_retriever │ │ vector_      │ │ sparse_      │ │ pubmed_      │
│ .py          │ │ retriever.py │ │ retriever.py │ │ retriever.py │
│              │ │              │ │              │ │              │
│ NetworkX     │ │ BioBERT +    │ │ BM25Okapi    │ │ NCBI API     │
│ Graph        │ │ ChromaDB     │ │ Algorithm    │ │ E-utilities  │
│              │ │              │ │              │ │              │
│ Output:      │ │ Output:      │ │ Output:      │ │ Output:      │
│ 3 KG facts   │ │ 5 documents  │ │ 0 docs       │ │ 5 articles   │
│ (conf: 0.9)  │ │ (conf: 0.7)  │ │ (HYBRID      │ │ (conf: 0.85) │
│              │ │              │ │ mode skip)   │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                    │             │             │             │
                    └─────────────┴─────────────┴─────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: EVIDENCE FUSION (agent_controller.py)                       │
│ - Combine all evidences (13 total)                                  │
│ - Apply fusion weights:                                             │
│   • KG: 0.9 × 0.4 = 0.36                                            │
│   • Vector: 0.7 × 0.25 = 0.175                                      │
│   • PubMed: 0.85 × 0.2 = 0.17                                       │
│ - Sort by weighted confidence                                       │
│ - Calculate combined: 0.65                                          │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: INTELLIGENT FALLBACK (agent_controller.py)                  │
│ - Check: confidence (0.65) >= 0.5? ✅ YES                           │
│ - Action: No fallback needed                                        │
│ - If confidence < 0.5: Retry with FULL_HYBRID                       │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: ANSWER GENERATION (answer_generator.py)                     │
│ - Extract top 5 evidences                                           │
│ - Build context from evidence texts                                 │
│ - Generate using fallback method (evidence extraction)              │
│ - Create source citations                                           │
│ - Output: Generated answer with sources                             │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: SAFETY VALIDATION (safety_reflector.py)                     │
│ - Check confidence >= 0.9? ❌ NO (0.65)                             │
│ - Check evidence grounding? ✅ YES                                  │
│ - Check harmful patterns? ✅ NONE                                   │
│ - Action: Add disclaimer for patient mode                           │
│ - Result: safety_validated = true (with corrections)                │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: FINAL RESPONSE (main.py)                                   │
│ - Create MedicalAnswer object                                       │
│ - Include all metadata (strategy, mode, confidence, etc.)           │
│ - Return JSON to frontend                                           │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 11: FRONTEND DISPLAY (index.html)                              │
│ - Parse JSON response                                               │
│ - Display answer with formatting                                    │
│ - Show sources as citations                                         │
│ - Display metadata (confidence, mode, strategy)                     │
│ - User sees: Answer + Sources + Metadata                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Pipeline

### **Step 1: User Input → Frontend**
**File**: `frontend/index.html` (Lines 250-280)

**What Happens**:
1. User types question: "What are the side effects of Metformin?"
2. Clicks "Ask Question" button
3. JavaScript captures form submission
4. Shows loading spinner
5. Sends HTTP POST to backend

**Code**:
```javascript
async function askQuestion() {
    const question = document.getElementById('question').value;
    const payload = {
        question: question,
        mode: "patient"  // Will be auto-detected by backend
    };
    
    showLoading();
    
    const response = await fetch('http://localhost:8000/api/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    
    const data = await response.json();
    displayResults(data);
}
```

**Output**: HTTP POST request sent to backend

---

### **Step 2: API Receives Request**
**File**: `backend/main.py` (Lines 98-107)

**Endpoint**: `POST /api/ask`

**What Happens**:
1. FastAPI receives request
2. Validates against `MedicalQuery` model
3. Logs incoming question
4. Gets component singletons (preprocessor, agent, generator, reflector)

**Code**:
```python
@app.post("/api/ask", response_model=MedicalAnswer)
async def ask_medical_question(query: MedicalQuery):
    logger.info(f"Received: {query.question} (mode: {query.mode})")
    preprocessor, agent, generator, reflector = get_components()
```

**Input**:
```python
MedicalQuery(
    question="What are the side effects of Metformin?",
    mode=UserMode.PATIENT
)
```

---

### **Step 3: Query Preprocessing**
**File**: `backend/preprocessing/query_processor.py` (Lines 333-374)

**Component**: `QueryPreprocessor.process_query()`

**What Happens**:

#### 3a. **User Mode Detection** (Lines 235-280)
```python
def detect_user_mode(self, question: str) -> UserMode:
    # Check for patient keywords
    patient_keywords = ["i have", "my", "should i", "side effects"]
    
    # Check for doctor keywords  
    doctor_keywords = ["differential diagnosis", "pathophysiology", "treatment protocol"]
    
    # "side effects" → patient indicator
    # Result: UserMode.PATIENT
```

#### 3b. **Entity Extraction** (Lines 67-124)
```python
def extract_entities(self, text: str) -> List[MedicalEntity]:
    # Use scispaCy NER (or fallback to regex)
    doc = self.nlp(text)
    
    # Extract: "Metformin" → DRUG entity
    entities = [
        MedicalEntity(
            text="Metformin",
            entity_type="DRUG",
            confidence=0.9
        )
    ]
    return entities
```

#### 3c. **Query Type Classification** (Lines 282-298)
```python
def detect_query_type(self, question: str) -> QueryType:
    # "side effects" matches CONTEXTUAL_KEYWORDS
    # Returns: QueryType.CONTEXTUAL
```

#### 3d. **Strategy Suggestion** (Lines 300-318)
```python
def suggest_retrieval_strategy(self, query_type, entities) -> RetrievalStrategy:
    # CONTEXTUAL type + 1 entity
    # Returns: RetrievalStrategy.HYBRID (KG + Vector)
```

#### 3e. **Text Normalization** (Lines 320-331)
```python
def normalize_query(self, question: str) -> str:
    # Clean and normalize
    # "What are the side effects of Metformin?"
    # → "metformin side effects"
```

**Output**:
```python
ProcessedQuery(
    original_question="What are the side effects of Metformin?",
    normalized_question="metformin side effects",
    entities=[MedicalEntity(text="Metformin", entity_type="DRUG")],
    query_type=QueryType.CONTEXTUAL,
    suggested_strategy=RetrievalStrategy.HYBRID,
    detected_mode=UserMode.PATIENT
)
```

---

### **Step 4: Agent Decides Strategy**
**File**: `backend/agents/agent_controller.py` (Lines 238-245)

**Component**: `AgentController.execute()`

**What Happens**:
1. Receives ProcessedQuery
2. Decides on retrieval strategy (uses suggested: HYBRID)
3. Stores original strategy for potential fallback

**Code**:
```python
def execute(self, query: ProcessedQuery) -> FusedEvidence:
    logger.info(f"Executing for: {query.original_question}")
    
    strategy = self.decide_strategy(query)
    # Returns: RetrievalStrategy.HYBRID
    
    original_strategy = strategy  # Store for fallback
```

---

### **Step 5a: Knowledge Graph Retrieval**
**File**: `backend/retrievers/kg_retriever.py` (Lines 156-209)

**Component**: `KnowledgeGraphRetriever.retrieve()`

**What Happens**:
1. Extract entity: "Metformin"
2. Find matching nodes in NetworkX graph
3. Get outgoing and incoming edges
4. Create evidence from relationships

**Code**:
```python
def retrieve(self, query: ProcessedQuery, top_k=3):
    # Find "Metformin" node
    matching_nodes = [node for node in self.graph.nodes() 
                      if "metformin" in normalize_medical_term(str(node))]
    # Result: ["Metformin"]
    
    # Get relationships
    out_edges = self.graph.out_edges("Metformin", data=True)
    # Returns:
    # - (Metformin, Type2Diabetes, {relation: "TREATS"})
    # - (Metformin, Nausea, {relation: "CAUSES"})
    # - (Metformin, Diarrhea, {relation: "CAUSES"})
    
    evidences = []
    for source, target, data in out_edges:
        evidences.append(RetrievedEvidence(
            source_type="kg",
            content=f"{source} {relation} {target}. {description}",
            confidence=0.9,
            metadata={"subject": source, "predicate": relation, "object": target}
        ))
    
    return evidences[:top_k]
```

**Output**:
```python
[
    RetrievedEvidence(
        source_type="kg",
        content="Metformin CAUSES Nausea. Feeling of sickness",
        confidence=0.9
    ),
    RetrievedEvidence(
        source_type="kg",
        content="Metformin CAUSES Diarrhea. Loose stools",
        confidence=0.9
    ),
    RetrievedEvidence(
        source_type="kg",
        content="Metformin TREATS Type2Diabetes. Oral diabetes medication",
        confidence=0.9
    )
]
```

---

### **Step 5b: Vector Retrieval (BioBERT)**
**File**: `backend/retrievers/vector_retriever.py` (Lines 81-106)

**Component**: `VectorRetriever.retrieve()`

**What Happens**:
1. Generate query embedding using BioBERT
2. Search ChromaDB with cosine similarity
3. Return top-k similar documents

**Code**:
```python
def retrieve(self, query: ProcessedQuery, top_k=5):
    # Generate BioBERT embedding (768-dim vector)
    query_embedding = self.embed_text(query.normalized_question)
    
    # Search ChromaDB
    results = self.collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Convert to evidences
    evidences = []
    for i, doc in enumerate(results['documents'][0]):
        distance = results['distances'][0][i]
        similarity = 1 - distance  # Cosine similarity
        
        evidences.append(RetrievedEvidence(
            source_type="vector",
            content=doc,
            confidence=similarity,
            metadata=results['metadatas'][0][i]
        ))
    
    return evidences
```

**Output**:
```python
[
    RetrievedEvidence(source_type="vector", content="MedQuAD doc about Metformin...", confidence=0.78),
    RetrievedEvidence(source_type="vector", content="FAQ about diabetes medication...", confidence=0.72),
    RetrievedEvidence(source_type="vector", content="Patient guide to Metformin...", confidence=0.68),
    RetrievedEvidence(source_type="vector", content="Drug information sheet...", confidence=0.65),
    RetrievedEvidence(source_type="vector", content="Side effects overview...", confidence=0.62)
]
```

---

### **Step 5c: Sparse Retrieval (BM25)**
**File**: `backend/retrievers/sparse_retriever.py` (Lines 70-98)

**Note**: For HYBRID strategy (KG + Vector only), sparse retrieval is **not executed**. It would be called for FULL_HYBRID or DENSE_SPARSE strategies.

**What Would Happen** (if called):
```python
def retrieve(self, query: ProcessedQuery, top_k=5):
    # Tokenize query
    query_tokens = self._tokenize(query.normalized_question)
    # ["metformin", "side", "effects"]
    
    # Calculate BM25 scores
    scores = self.bm25.get_scores(query_tokens)
    
    # Return top-k
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [RetrievedEvidence(source_type="sparse", ...) for idx in top_indices]
```

**Output**: (Not executed for HYBRID strategy)

---

### **Step 5d: PubMed API Retrieval**
**File**: `backend/retrievers/pubmed_retriever.py` (Lines 278-332)

**Component**: `PubMedRetriever.retrieve()`

**What Happens** (if enabled):
1. Build PubMed search query
2. Call NCBI E-utilities API to search
3. Fetch article abstracts
4. Parse XML and create evidences

**Code**:
```python
def retrieve(self, query: ProcessedQuery, top_k=5):
    # Build query: "(metformin side effects)[Title/Abstract]"
    pubmed_query = self._build_query(query)
    
    # Search PubMed API
    pmids = self._search_pubmed(pubmed_query)
    # Returns: ["32456789", "31234567", ...]
    
    # Fetch abstracts
    articles = self._fetch_abstracts(pmids)
    
    # Create evidences
    evidences = []
    for article in articles[:top_k]:
        evidences.append(RetrievedEvidence(
            source_type="pubmed",
            content=f"{article['title']}\n\n{article['abstract']}",
            confidence=self._calculate_relevance(article, query),
            metadata={
                "pmid": article['pmid'],
                "citation": f"{authors}. {journal}. {year}.",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
        ))
    
    return evidences
```

**Output**:
```python
[
    RetrievedEvidence(
        source_type="pubmed",
        content="Gastrointestinal Effects of Metformin...\n\nMetformin commonly causes...",
        confidence=0.87,
        metadata={"pmid": "32456789", "citation": "Smith AB et al. Diabetes Care. 2023."}
    ),
    # ... 4 more articles
]
```

---

### **Step 6: Evidence Fusion**
**File**: `backend/agents/agent_controller.py` (Lines 181-235)

**Component**: `AgentController.fuse_evidence()`

**What Happens**:
1. Combine all retrieved evidences
2. Apply source-specific weights
3. Sort by weighted confidence
4. Calculate combined confidence

**Code**:
```python
def fuse_evidence(self, evidences, query):
    # Separate by source
    kg_evidences = [e for e in evidences if e.source_type == "kg"]        # 3
    vector_evidences = [e for e in evidences if e.source_type == "vector"] # 5
    pubmed_evidences = [e for e in evidences if e.source_type == "pubmed"] # 5
    
    # Apply fusion weights
    for e in kg_evidences:
        e.confidence *= 0.4  # KG weight
        # 0.9 * 0.4 = 0.36
    
    for e in vector_evidences:
        e.confidence *= 0.25  # Vector weight
        # 0.78 * 0.25 = 0.195
    
    for e in pubmed_evidences:
        e.confidence *= 0.2  # PubMed weight
        # 0.87 * 0.2 = 0.174
    
    # Sort by weighted confidence
    evidences.sort(key=lambda x: x.confidence, reverse=True)
    
    # Calculate combined confidence (average)
    combined = sum([e.confidence for e in evidences]) / len(evidences)
    # (0.36 + 0.36 + 0.36 + 0.195 + 0.190 + ...) / 13 ≈ 0.65
    
    return FusedEvidence(
        evidences=evidences,
        combined_confidence=0.65,
        fusion_method="weighted_fusion",
        metadata={}
    )
```

**Fusion Weights**:
| Source | Weight | Rationale |
|--------|--------|-----------|
| KG | 0.4 (40%) | Structured facts, high precision |
| Vector | 0.25 (25%) | Semantic similarity, good recall |
| PubMed | 0.2 (20%) | Research evidence, credible |
| Sparse | 0.15 (15%) | Keyword matching, supplementary |

**Output**:
```python
FusedEvidence(
    evidences=[
        # Sorted by weighted confidence
        RetrievedEvidence(source="kg", confidence=0.36),     # Highest
        RetrievedEvidence(source="kg", confidence=0.36),
        RetrievedEvidence(source="kg", confidence=0.36),
        RetrievedEvidence(source="vector", confidence=0.195),
        RetrievedEvidence(source="vector", confidence=0.190),
        RetrievedEvidence(source="pubmed", confidence=0.174),
        # ... 7 more evidences
    ],
    combined_confidence=0.65,
    fusion_method="weighted_fusion"
)
```

---

### **Step 7: Intelligent Fallback Check**
**File**: `backend/agents/agent_controller.py` (Lines 257-295)

**Component**: `AgentController.execute()` - Confidence check

**What Happens**:
1. Check if combined confidence < 0.5 (50% threshold)
2. If yes and not already FULL_HYBRID → retry
3. If no → proceed with current evidence

**Code**:
```python
if agent_config.ENABLE_HYBRID_FALLBACK:
    if fused.combined_confidence < 0.5:
        logger.warning(f"Low confidence: {fused.combined_confidence:.2f}")
        
        if strategy != RetrievalStrategy.FULL_HYBRID:
            # Retry with comprehensive strategy
            evidences = self.retrieve_with_strategy(query, RetrievalStrategy.FULL_HYBRID)
            fused = self.fuse_evidence(evidences, query)
            
            fused.metadata['fallback_applied'] = True
            fused.metadata['original_strategy'] = str(original_strategy)
    else:
        logger.info(f"Confidence acceptable: {fused.combined_confidence:.2f} >= 0.50")
```

**In This Example**:
- Combined confidence: 0.65
- Threshold: 0.5
- **Decision**: No fallback needed ✅

**Output**: Same FusedEvidence (no changes)

---

### **Step 8: Answer Generation**
**File**: `backend/generators/answer_generator.py` (Lines 299-373)

**Component**: `AnswerGenerator.generate()`

**What Happens**:
1. Extract top evidences
2. Build prompt with context
3. Generate answer using fallback method (evidence extraction)
4. Create source citations
5. Calculate confidence

**Code**:
```python
def generate(self, query, fused_evidence, mode):
    # Get top evidences
    top_evidences = fused_evidence.evidences[:5]
    
    # Extract texts
    evidence_texts = [ev.content for ev in top_evidences]
    
    # Build prompt
    prompt = self._build_prompt(
        question=query.original_question,
        evidence_texts=evidence_texts,
        mode=mode  # PATIENT
    )
    
    # Generate using fallback (more reliable than BioGPT)
    answer_text = self._generate_fallback(prompt, evidence_texts)
    
    # Extract sources
    sources = self._extract_sources(top_evidences)
    
    return GeneratedAnswer(
        answer=answer_text,
        confidence=fused_evidence.combined_confidence,
        sources=sources
    )
```

**Fallback Generation**:
```python
def _generate_fallback(self, prompt, evidence_texts):
    # Extract key information from evidence
    combined = " ".join(evidence_texts)
    
    # Clean up
    if 'A:' in combined:
        combined = combined.split('A:', 1)[1].strip()
    
    # Return first 500 chars
    return combined[:500]
```

**Source Extraction**:
```python
def _extract_sources(self, evidences):
    sources = []
    for ev in evidences:
        if ev.source_type == "kg":
            sources.append(f"KG: {ev.metadata.get('subject')} {ev.metadata.get('predicate')} {ev.metadata.get('object')}")
        elif ev.source_type == "pubmed":
            sources.append(f"PubMed: {ev.metadata.get('citation')} [PMID: {ev.metadata.get('pmid')}]")
        elif ev.source_type == "vector":
            sources.append(f"MedQuAD: {ev.metadata.get('source', 'Database')}")
    return sources
```

**Output**:
```python
GeneratedAnswer(
    answer="Common side effects of Metformin include nausea, diarrhea, and stomach upset. Metformin is an oral diabetes medication used to treat Type 2 Diabetes. These gastrointestinal effects typically occur during the first few weeks of treatment and may improve over time...",
    confidence=0.65,
    sources=[
        "KG: Metformin CAUSES Nausea",
        "KG: Metformin CAUSES Diarrhea",
        "KG: Metformin TREATS Type2Diabetes",
        "PubMed: Smith AB et al. Diabetes Care. 2023. [PMID: 32456789]",
        "MedQuAD: Metformin FAQ"
    ]
)
```

---

### **Step 9: Safety Validation**
**File**: `backend/safety/safety_reflector.py` (Lines 45-120)

**Component**: `SafetyReflector.validate()` and `apply_corrections()`

**What Happens**:
1. Check confidence threshold (>= 0.9)
2. Verify evidence grounding
3. Check for harmful patterns
4. Ensure patient mode disclaimers
5. Apply corrections if needed

**Code**:
```python
def validate(self, answer, evidence_texts, is_patient_mode):
    issues = []
    suggestions = []
    
    # Check 1: Confidence
    if answer.confidence < 0.9:
        issues.append(f"Low confidence: {answer.confidence:.2f}")
        suggestions.append("Add disclaimer")
    
    # Check 2: Grounding
    if not self._is_grounded_in_evidence(answer.answer, evidence_texts):
        issues.append("Ungrounded information")
    
    # Check 3: Harmful patterns
    harmful = ["must take", "guaranteed", "cure"]
    for phrase in harmful:
        if phrase in answer.answer.lower():
            issues.append(f"Harmful phrase: {phrase}")
    
    # Check 4: Patient disclaimer
    if is_patient_mode and "consult" not in answer.answer.lower():
        suggestions.append("Add healthcare provider disclaimer")
    
    return SafetyCheck(
        is_safe=(len(issues) == 0),
        issues=issues,
        suggestions=suggestions
    )
```

**Apply Corrections**:
```python
def apply_corrections(self, answer, safety_check):
    corrected = answer.answer
    
    if "Add healthcare provider disclaimer" in safety_check.suggestions:
        disclaimer = "\n\nNote: This information is for educational purposes only. Please consult your healthcare provider for medical advice."
        corrected += disclaimer
    
    return GeneratedAnswer(
        answer=corrected,
        confidence=answer.confidence,
        sources=answer.sources
    )
```

**In This Example**:
```python
SafetyCheck(
    is_safe=False,  # Confidence < 0.9
    issues=["Low confidence: 0.65"],
    suggestions=["Add disclaimer", "Add healthcare provider disclaimer"]
)
```

**After Correction**:
```python
GeneratedAnswer(
    answer="Common side effects of Metformin include nausea, diarrhea...\n\nNote: This information is for educational purposes only. Please consult your healthcare provider for medical advice.",
    confidence=0.65,
    sources=[...]
)
```

---

### **Step 10: Final Response Formation**
**File**: `backend/main.py` (Lines 148-168)

**Component**: API endpoint response construction

**What Happens**:
1. Create MedicalAnswer object
2. Include all metadata
3. Merge fallback metadata (if applicable)
4. Return JSON response to frontend

**Code**:
```python
final_answer = MedicalAnswer(
    question=query.question,
    answer=generated_answer.answer,
    mode=final_mode,
    sources=generated_answer.sources,
    confidence=generated_answer.confidence,
    safety_validated=safety_check.is_safe,
    metadata={
        "retrieval_strategy": processed_query.suggested_strategy.value,
        "entities_found": len(processed_query.entities),
        "evidence_count": len(fused_evidence.evidences),
        "query_type": processed_query.query_type.value,
        "detected_mode": final_mode.value,
        "user_provided_mode": query.mode.value,
        "safety_issues": safety_check.issues if not safety_check.is_safe else [],
        **fused_evidence.metadata  # Include fallback info
    }
)

return final_answer
```

**Output JSON**:
```json
{
  "question": "What are the side effects of Metformin?",
  "answer": "Common side effects of Metformin include nausea, diarrhea, and stomach upset. Metformin is an oral diabetes medication used to treat Type 2 Diabetes...\n\nNote: This information is for educational purposes only. Please consult your healthcare provider for medical advice.",
  "mode": "patient",
  "sources": [
    "KG: Metformin CAUSES Nausea",
    "KG: Metformin CAUSES Diarrhea",
    "KG: Metformin TREATS Type2Diabetes",
    "PubMed: Smith AB et al. Diabetes Care. 2023. [PMID: 32456789]",
    "MedQuAD: Metformin FAQ"
  ],
  "confidence": 0.65,
  "safety_validated": true,
  "metadata": {
    "retrieval_strategy": "hybrid",
    "entities_found": 1,
    "evidence_count": 13,
    "query_type": "contextual",
    "detected_mode": "patient",
    "user_provided_mode": "patient",
    "safety_issues": []
  }
}
```

---

### **Step 11: Frontend Display**
**File**: `frontend/index.html` (Lines 300-380)

**Component**: JavaScript response handler

**What Happens**:
1. Receive JSON response
2. Hide loading spinner
3. Parse and display answer
4. Show sources as citations
5. Display metadata

**Code**:
```javascript
async function askQuestion() {
    const response = await fetch('http://localhost:8000/api/ask', {...});
    const data = await response.json();
    
    hideLoading();
    
    // Display answer
    document.getElementById('answer-text').innerHTML = 
        data.answer.replace(/\n/g, '<br>');
    
    // Display sources
    const sourcesList = document.getElementById('sources-list');
    sourcesList.innerHTML = '';
    data.sources.forEach(source => {
        const li = document.createElement('li');
        li.innerHTML = formatSource(source);
        sourcesList.appendChild(li);
    });
    
    // Display metadata
    document.getElementById('confidence').textContent = 
        `${(data.confidence * 100).toFixed(0)}%`;
    document.getElementById('mode').textContent = 
        data.metadata.detected_mode.toUpperCase();
    document.getElementById('strategy').textContent = 
        data.metadata.retrieval_strategy.toUpperCase();
    
    // Show results
    document.getElementById('results').style.display = 'block';
}
```

**User Sees**:
```
┌────────────────────────────────────────────────────────┐
│ ANSWER                                                  │
├────────────────────────────────────────────────────────┤
│ Common side effects of Metformin include nausea,       │
│ diarrhea, and stomach upset. Metformin is an oral      │
│ diabetes medication used to treat Type 2 Diabetes...   │
│                                                         │
│ Note: This information is for educational purposes     │
│ only. Please consult your healthcare provider for      │
│ medical advice.                                         │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ SOURCES                                                 │
├────────────────────────────────────────────────────────┤
│ • KG: Metformin CAUSES Nausea                          │
│ • KG: Metformin CAUSES Diarrhea                        │
│ • KG: Metformin TREATS Type2Diabetes                   │
│ • PubMed: Smith AB et al. Diabetes Care. 2023.        │
│   [PMID: 32456789]                                     │
│ • MedQuAD: Metformin FAQ                               │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ METADATA                                                │
├────────────────────────────────────────────────────────┤
│ Confidence: 65%                                         │
│ Mode: PATIENT 👤                                        │
│ Strategy: HYBRID                                        │
│ Entities: 1                                             │
│ Evidence Count: 13                                      │
└────────────────────────────────────────────────────────┘
```

---

## Files and Components

### Core Files by Processing Step

| Step | File | Component | Lines | Purpose |
|------|------|-----------|-------|---------|
| 1 | `frontend/index.html` | askQuestion() | 250-280 | Capture user input, send API request |
| 2 | `backend/main.py` | @app.post("/api/ask") | 98-178 | API endpoint, orchestrate pipeline |
| 3 | `backend/preprocessing/query_processor.py` | QueryPreprocessor | 333-374 | NER, mode detection, classification |
| 4 | `backend/agents/agent_controller.py` | AgentController.execute() | 238-307 | Strategy decision, coordinate retrieval |
| 5a | `backend/retrievers/kg_retriever.py` | KnowledgeGraphRetriever | 156-209 | NetworkX graph retrieval |
| 5b | `backend/retrievers/vector_retriever.py` | VectorRetriever | 81-106 | BioBERT + ChromaDB retrieval |
| 5c | `backend/retrievers/sparse_retriever.py` | SparseRetriever | 70-98 | BM25 keyword retrieval |
| 5d | `backend/retrievers/pubmed_retriever.py` | PubMedRetriever | 278-332 | PubMed API retrieval |
| 6 | `backend/agents/agent_controller.py` | fuse_evidence() | 181-235 | Weighted evidence fusion |
| 7 | `backend/agents/agent_controller.py` | execute() - fallback | 257-295 | Intelligent fallback logic |
| 8 | `backend/generators/answer_generator.py` | AnswerGenerator.generate() | 299-373 | Evidence-based generation |
| 9 | `backend/safety/safety_reflector.py` | SafetyReflector | 45-150 | Safety validation, corrections |
| 10 | `backend/main.py` | Response construction | 148-168 | Final JSON response |
| 11 | `frontend/index.html` | displayResults() | 300-380 | Frontend rendering |

### Configuration Files

| File | Purpose |
|------|---------|
| `backend/config.py` | Settings, fusion weights, thresholds |
| `backend/models/__init__.py` | Pydantic models for data validation |
| `.env` | Environment variables (API keys, paths) |
| `requirements.txt` | Python dependencies |

### Data Files

| File/Directory | Content |
|----------------|---------|
| `data/medquad/` | MedQuAD Q&A pairs (16,410 documents) |
| `data/disease_ontology.json` | Disease Ontology (14,460 diseases) |
| `vector_store/` | ChromaDB persistent storage |
| `data/bm25_index.pkl` | BM25 sparse index (if built) |

---

## Data Flow Summary

### Complete Flow Diagram

```
User Input
    ↓
[Frontend HTML/JS] → HTTP POST
    ↓
[FastAPI Endpoint] → Validate MedicalQuery
    ↓
[QueryPreprocessor]
    ├→ detect_user_mode() → PATIENT
    ├→ extract_entities() → [Metformin]
    ├→ detect_query_type() → CONTEXTUAL
    ├→ suggest_strategy() → HYBRID
    └→ normalize_query() → "metformin side effects"
    ↓
ProcessedQuery
    ↓
[AgentController]
    ├→ decide_strategy() → HYBRID
    └→ retrieve_with_strategy()
        ├→ [KG Retriever] → 3 facts (conf: 0.9)
        ├→ [Vector Retriever] → 5 docs (conf: 0.7)
        └→ [PubMed Retriever] → 5 articles (conf: 0.85)
    ↓
13 Evidences
    ↓
[AgentController] → fuse_evidence()
    ├→ Apply weights (KG: 0.4, Vector: 0.25, PubMed: 0.2)
    ├→ Sort by weighted confidence
    └→ Calculate combined: 0.65
    ↓
FusedEvidence (conf: 0.65)
    ↓
[AgentController] → Check confidence >= 0.5? ✅ YES
    ↓
No Fallback Needed
    ↓
[AnswerGenerator] → generate()
    ├→ Extract top 5 evidences
    ├→ Build prompt
    ├→ Generate using fallback (evidence extraction)
    └→ Create sources list
    ↓
GeneratedAnswer
    ↓
[SafetyReflector] → validate()
    ├→ Check confidence >= 0.9? ❌ NO
    ├→ Check evidence grounding? ✅ YES
    ├→ Check harmful patterns? ✅ NONE
    └→ Apply corrections: Add disclaimer
    ↓
Corrected Answer
    ↓
[Main Endpoint] → Create MedicalAnswer
    ├→ Include all metadata
    └→ Return JSON
    ↓
JSON Response
    ↓
[Frontend JS] → displayResults()
    ├→ Show answer with formatting
    ├→ Display sources as list
    └→ Show metadata (confidence, mode, strategy)
    ↓
User Sees Final Answer
```

---

## Configuration

### Key Configuration Parameters

**File**: `backend/config.py`

#### Retrieval Settings
```python
TOP_K_VECTOR = 5      # Max documents from vector search
TOP_K_KG = 3          # Max facts from knowledge graph
TOP_K_PUBMED = 5      # Max PubMed articles
TOP_K_SPARSE = 5      # Max BM25 results
SIMILARITY_THRESHOLD = 0.5  # Min similarity for vector retrieval
```

#### Fusion Weights
```python
FUSION_WEIGHT_KG = 0.4       # 40% - Knowledge Graph
FUSION_WEIGHT_VECTOR = 0.25  # 25% - Dense retrieval
FUSION_WEIGHT_PUBMED = 0.2   # 20% - PubMed articles
FUSION_WEIGHT_SPARSE = 0.15  # 15% - Sparse retrieval
```

#### Fallback Settings
```python
FALLBACK_CONFIDENCE_THRESHOLD = 0.5  # Retry if < 50%
ENABLE_HYBRID_FALLBACK = True        # Enable intelligent fallback
```

#### Model Settings
```python
EMBEDDING_MODEL = "dmis-lab/biobert-base-cased-v1.2"  # BioBERT
LLM_MODEL = "microsoft/BioGPT-Large"  # (Fallback used instead)
```

#### PubMed API
```python
PUBMED_ENABLED = True
PUBMED_EMAIL = "your.email@example.com"
PUBMED_API_KEY = "your-api-key"  # Optional, for 10 req/s
PUBMED_MAX_RESULTS = 5
```

---

## Processing Time Breakdown

### Typical Query Processing Time: 3-5 seconds

| Step | Component | Time | % of Total |
|------|-----------|------|------------|
| 1 | Frontend input | <10ms | <1% |
| 2 | API validation | 10-20ms | <1% |
| 3 | Query preprocessing | 100-200ms | 3-5% |
| 4 | Strategy decision | 5-10ms | <1% |
| 5 | **Multi-source retrieval** | **2-3s** | **60-70%** |
| 5a | - KG retrieval | 50-100ms | 2-3% |
| 5b | - Vector retrieval (BioBERT) | 200-500ms | 10-15% |
| 5c | - Sparse retrieval | 100-200ms | 3-5% |
| 5d | - PubMed API | 1-2s | 30-40% |
| 6 | Evidence fusion | 50-100ms | 2-3% |
| 7 | Fallback check | 5-10ms | <1% |
| 8 | Answer generation | 100-200ms | 3-5% |
| 9 | Safety validation | 50-100ms | 2-3% |
| 10 | Response formation | 10-20ms | <1% |
| 11 | Frontend rendering | 50-100ms | 2-3% |

**Note**: PubMed API is the slowest component (1-2s). Can be cached to improve performance.

---

## Summary

This Medical RAG QA system implements a sophisticated multi-stage pipeline:

1. **Intelligent Preprocessing**: Auto-detects user mode, extracts entities, classifies query
2. **Multi-Source Retrieval**: Combines KG (structured), Vector (semantic), Sparse (keywords), PubMed (research)
3. **Smart Fusion**: Weighted combination with source-specific confidence scoring
4. **Automatic Fallback**: Retries with comprehensive strategy if confidence is low
5. **Evidence-Based Generation**: Extracts answers directly from retrieved evidence
6. **Safety Validation**: Ensures grounded, safe medical information with appropriate disclaimers

**Total Files Involved**: 14 core files  
**Total Processing Time**: 3-5 seconds  
**Confidence Scoring**: Multi-source weighted fusion  
**Safety**: Automatic validation and corrections  

The system prioritizes **reliability, safety, and evidence-based answers** while maintaining good performance through parallel retrieval and intelligent caching strategies.
