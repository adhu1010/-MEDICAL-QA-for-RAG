# PubMed Dynamic API Integration Guide

## 🎯 Overview

Your Medical RAG system now includes **real-time PubMed literature retrieval** that dynamically fetches relevant research articles from 30+ million PubMed entries for each query.

### Key Features:
✅ **Real-time**: Fetches latest research articles on-demand  
✅ **Evidence-based**: 5 citations per answer from peer-reviewed journals  
✅ **Zero storage**: No large downloads required (~0 MB)  
✅ **NCBI E-utilities API**: Official PubMed API integration  
✅ **Rate-limited**: Respects API limits (3 req/s or 10 req/s with key)  
✅ **Automatic**: Integrates seamlessly with existing retrievers  

---

## 🚀 Quick Setup

### Step 1: Set Your Email (Required)

NCBI requires an email address for API access:

**Windows PowerShell**:
```powershell
$env:PUBMED_EMAIL="your.email@example.com"
```

**Linux/Mac**:
```bash
export PUBMED_EMAIL="your.email@example.com"
```

**Or add to `.env` file**:
```bash
PUBMED_ENABLED=true
PUBMED_EMAIL=your.email@example.com
PUBMED_MAX_RESULTS=5
```

### Step 2: Optional - Get API Key (Higher Rate Limits)

For faster retrieval (10 req/s instead of 3 req/s):

1. Create NCBI account: https://www.ncbi.nlm.nih.gov/account/
2. Go to **Settings → API Key Management**
3. Create new API key
4. Add to `.env`:

```bash
PUBMED_API_KEY=your-api-key-here
```

### Step 3: Restart Backend

```bash
python scripts/run.py
```

**That's it!** PubMed integration is now active.

---

## 🔄 How It Works

### Complete Pipeline

```
User Query: "What are the treatments for diabetes?"
           ↓
┌──────────────────────────────────────────────────┐
│ 1. QUERY PREPROCESSING                           │
│    Entities: ["diabetes", "treatments"]          │
└──────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│ 2. AGENT RETRIEVAL STRATEGY                      │
│    Strategy: FULL_HYBRID + PubMed                │
│    Sources: KG + Dense + Sparse + PubMed         │
└──────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│ 3. PUBMED REAL-TIME SEARCH                       │
│    Query: "(diabetes treatments)[Title/Abstract]"│
│    API Call: NCBI E-utilities esearch            │
│    Result: 5 PMIDs (article IDs)                 │
└──────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│ 4. FETCH ARTICLE ABSTRACTS                       │
│    API Call: NCBI E-utilities efetch             │
│    Parse XML: Title, Abstract, Authors, Journal  │
│    Result: 5 full articles with metadata         │
└──────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│ 5. EVIDENCE FUSION                               │
│    KG: 3 facts × 0.4 weight = 1.2               │
│    Vector: 5 docs × 0.25 weight = 1.25          │
│    Sparse: 5 docs × 0.15 weight = 0.75          │
│    PubMed: 5 articles × 0.2 weight = 1.0        │
│    Combined: 18 evidences, sorted by score       │
└──────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│ 6. ANSWER GENERATION                             │
│    Top evidences (PubMed articles ranked high)   │
│    Generate answer with citations                │
│    Include: PMID, authors, journal, year         │
└──────────────────────────────────────────────────┘
```

---

## 📊 Integration Architecture

### Source Weights (Updated)

| Source | Weight | Purpose | Confidence |
|--------|--------|---------|------------|
| **KG** | 0.4 | Structured facts | 0.9 |
| **Vector (Dense)** | 0.25 | Semantic search | 0.6-0.8 |
| **PubMed** | 0.2 | Research literature | 0.7-0.95 |
| **Sparse (BM25)** | 0.15 | Keyword matching | 0.6-0.7 |

**Total**: 1.0 (normalized)

### Why PubMed Gets 0.2 Weight?
- ✅ Peer-reviewed research (high quality)
- ✅ Up-to-date information (real-time)
- ✅ Credible sources (journals, authors)
- ⚠️ May contain complex medical terminology
- ⚠️ Requires API call (slight latency)

---

## 🎯 Example Queries

### Example 1: Drug Side Effects

**Query**: "What are the side effects of Metformin?"

**PubMed Contribution**:
```json
{
  "pmid": "32456789",
  "title": "Gastrointestinal Adverse Effects of Metformin in Type 2 Diabetes",
  "abstract": "Metformin commonly causes gastrointestinal side effects including nausea, diarrhea, and abdominal discomfort...",
  "journal": "Diabetes Care",
  "year": "2023",
  "authors": ["Smith AB", "Johnson CD", "Williams EF"],
  "citation": "Smith AB, Johnson CD, Williams EF et al. Diabetes Care. 2023.",
  "url": "https://pubmed.ncbi.nlm.nih.gov/32456789/"
}
```

**Answer includes**:
- Side effects from research
- Citation: "Smith AB et al. Diabetes Care. 2023."
- Link to PubMed article

### Example 2: Treatment Options

**Query**: "How to treat hypertension in elderly patients?"

**PubMed Search**:
- Searches: `(hypertension treatment elderly)[Title/Abstract]`
- Fetches: 5 most relevant articles
- Includes: Clinical trials, systematic reviews, meta-analyses

**Answer provides**:
- Evidence-based treatment guidelines
- Citations from recent research (2023-2024)
- Links to full articles

### Example 3: Disease Information

**Query**: "What causes Alzheimer's disease?"

**Multi-source Answer**:
1. **KG**: Basic disease relationships
2. **Vector**: MedQuAD patient education
3. **PubMed**: Latest research on Alzheimer's etiology
4. **Sparse**: Keyword-matched documents

**Result**: Comprehensive answer with research backing

---

## ⚙️ Configuration Options

### In `.env` File

```bash
# PubMed Configuration
PUBMED_ENABLED=true              # Enable/disable PubMed retrieval
PUBMED_EMAIL=your@email.com      # Required for NCBI API
PUBMED_API_KEY=your-key-here     # Optional (for 10 req/s)
PUBMED_MAX_RESULTS=5             # Articles per query (default: 5)
TOP_K_PUBMED=5                   # Max articles to include in fusion
```

### In [`backend/config.py`](backend/config.py)

```python
# PubMed API Configuration
pubmed_email: Optional[str] = Field(None, env="PUBMED_EMAIL")
pubmed_api_key: Optional[str] = Field(None, env="PUBMED_API_KEY")
pubmed_enabled: bool = Field(True, env="PUBMED_ENABLED")
pubmed_max_results: int = Field(5, env="PUBMED_MAX_RESULTS")

# Retrieval Settings
top_k_pubmed: int = Field(5, env="TOP_K_PUBMED")
```

### Fusion Weights ([`backend/config.py`](backend/config.py))

```python
class AgentConfig:
    # Fusion weights (for weighted fusion method)
    FUSION_WEIGHT_KG = 0.4       # Knowledge Graph
    FUSION_WEIGHT_VECTOR = 0.25  # Dense retrieval
    FUSION_WEIGHT_PUBMED = 0.2   # Real-time literature (NEW!)
    FUSION_WEIGHT_SPARSE = 0.15  # Sparse (BM25)
```

**Adjust weights** based on your use case:
- **Research-focused**: Increase `FUSION_WEIGHT_PUBMED` to 0.3-0.4
- **Patient education**: Decrease to 0.1-0.15
- **Medical professionals**: Keep at 0.2-0.3

---

## 📈 Performance Impact

### API Call Latency

| Component | Time |
|-----------|------|
| Search (esearch) | 200-500ms |
| Fetch (efetch) | 500-1500ms |
| XML Parsing | 50-100ms |
| **Total** | **~1-2 seconds** |

**Total Query Time**:
- Without PubMed: ~2-3 seconds
- With PubMed: ~3-5 seconds (+1-2s)

### Rate Limits

**Without API Key**:
- 3 requests/second
- ~180 requests/minute

**With API Key**:
- 10 requests/second
- ~600 requests/minute

**Recommendation**: Get API key for production use.

### Caching (Future Enhancement)

To reduce latency, consider caching:
```python
# Cache PubMed results for 24 hours
# Key: query hash
# Value: articles
```

---

## 🔍 PubMed Retriever Details

### File: [`backend/retrievers/pubmed_retriever.py`](backend/retrievers/pubmed_retriever.py)

#### Key Methods:

**1. `_build_query()`** - Optimize search
```python
def _build_query(self, query: ProcessedQuery) -> str:
    # Combines normalized question + entities
    # Example: "(diabetes treatments)[Title/Abstract]"
    query_string = " ".join([query.normalized_question] + entity_terms)
    return f"({query_string})[Title/Abstract]"
```

**2. `_search_pubmed()` ** - Get article IDs
```python
def _search_pubmed(self, query_string: str) -> List[str]:
    # Uses NCBI esearch API
    # Returns: List of PMIDs (e.g., ["32456789", "31234567"])
```

**3. `_fetch_abstracts()`** - Get full articles
```python
def _fetch_abstracts(self, pmids: List[str]) -> List[dict]:
    # Uses NCBI efetch API
    # Returns: Articles with title, abstract, metadata
```

**4. `_parse_pubmed_xml()`** - Parse response
```python
def _parse_pubmed_xml(self, xml_data: str) -> List[dict]:
    # Parses PubMed XML format
    # Extracts: title, abstract, journal, year, authors
```

**5. `retrieve()`** - Main entry point
```python
def retrieve(self, query: ProcessedQuery, top_k: int = 5):
    # 1. Build optimized query
    # 2. Search PubMed
    # 3. Fetch abstracts
    # 4. Convert to RetrievedEvidence
    # 5. Return top_k results
```

---

## 🎓 Evidence Format

### PubMed Evidence Structure

```python
RetrievedEvidence(
    source_type="pubmed",
    content="Article Title\n\nFull abstract text...",
    confidence=0.85,  # Based on relevance
    metadata={
        "pmid": "32456789",
        "title": "Article Title",
        "journal": "Journal Name",
        "year": "2023",
        "authors": ["Smith AB", "Johnson CD"],
        "citation": "Smith AB, Johnson CD et al. Journal Name. 2023.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32456789/"
    }
)
```

### Citation Format in Answer

**Frontend Display**:
```
Answer: "Metformin commonly causes gastrointestinal side effects..."

Sources:
✓ PubMed: Smith AB et al. Diabetes Care. 2023. [PMID: 32456789]
✓ PubMed: Johnson CD et al. BMJ. 2024. [PMID: 33567890]
✓ MedQuAD: Diabetes Treatment FAQ
✓ KG: Metformin TREATS Type2Diabetes
```

---

## 🚦 Status Checking

### Check if PubMed is Enabled

```python
from backend.retrievers import get_pubmed_retriever

pubmed = get_pubmed_retriever()

if pubmed.enabled:
    print(f"✅ PubMed enabled (email: {pubmed.email})")
    print(f"   Rate: {'10 req/s' if pubmed.api_key else '3 req/s'}")
else:
    print("❌ PubMed disabled (no email configured)")
```

### Test PubMed Retrieval

```python
from backend.models import MedicalEntity, ProcessedQuery, QueryType, RetrievalStrategy, UserMode

# Create test query
query = ProcessedQuery(
    original_question="What are the side effects of aspirin?",
    normalized_question="aspirin side effects",
    entities=[
        MedicalEntity(text="aspirin", entity_type="DRUG", confidence=0.9)
    ],
    query_type=QueryType.CONTEXTUAL,
    suggested_strategy=RetrievalStrategy.FULL_HYBRID,
    detected_mode=UserMode.PATIENT
)

# Retrieve from PubMed
evidences = pubmed.retrieve(query, top_k=3)

for evidence in evidences:
    print(f"\n{'='*60}")
    print(f"PMID: {evidence.metadata['pmid']}")
    print(f"Title: {evidence.metadata['title']}")
    print(f"Journal: {evidence.metadata['journal']} ({evidence.metadata['year']})")
    print(f"Citation: {evidence.metadata['citation']}")
    print(f"Confidence: {evidence.confidence}")
    print(f"URL: {evidence.metadata['url']}")
    print(f"\nAbstract:\n{evidence.content[:200]}...")
```

---

## ⚠️ Troubleshooting

### Error: "PubMed retriever disabled (no email configured)"

**Solution**:
```bash
# Set email in .env
echo "PUBMED_EMAIL=your@email.com" >> .env

# Or set environment variable
$env:PUBMED_EMAIL="your@email.com"  # PowerShell
export PUBMED_EMAIL="your@email.com"  # Linux/Mac
```

### Error: "HTTP Error 429: Too Many Requests"

**Problem**: Exceeded rate limit

**Solution**:
1. Get NCBI API key (increases limit to 10 req/s)
2. Add to `.env`: `PUBMED_API_KEY=your-key-here`
3. Restart backend

### Error: "urllib.error.URLError: timed out"

**Problem**: Network timeout or NCBI API slow

**Solution**:
- Check internet connection
- Retry request
- Increase timeout in `pubmed_retriever.py`:
  ```python
  with urllib.request.urlopen(url, timeout=30) as response:  # Increase from 10
  ```

### Warning: "No PubMed articles found"

**Causes**:
1. Query too specific
2. No matching articles in PubMed
3. Network issue

**Solution**:
- Check logs for actual PubMed query
- Manually test on PubMed.gov
- Verify entity extraction is working

---

## 🎯 Best Practices

### 1. **Always Set Email**
```bash
# Required by NCBI
PUBMED_EMAIL=your.email@example.com
```

### 2. **Get API Key for Production**
- Increases rate limit 3x (3 → 10 req/s)
- Free from NCBI
- Takes 5 minutes to setup

### 3. **Adjust Results Based on Use Case**

**Patient Education** (simpler sources):
```bash
PUBMED_MAX_RESULTS=2  # Fewer, more relevant
FUSION_WEIGHT_PUBMED=0.1  # Lower weight
```

**Medical Research** (comprehensive):
```bash
PUBMED_MAX_RESULTS=10  # More articles
FUSION_WEIGHT_PUBMED=0.3  # Higher weight
```

### 4. **Monitor API Usage**

Check logs for PubMed activity:
```bash
# Look for:
# "PubMed search found X articles"
# "Fetched X PubMed abstracts"
# "Retrieved X PubMed evidences"
```

### 5. **Cache for Repeated Queries** (Future)

Implement caching to reduce API calls:
```python
# Pseudo-code
cache_key = hash(query.normalized_question)
if cache_key in redis_cache:
    return cached_articles
else:
    articles = fetch_from_pubmed()
    redis_cache.set(cache_key, articles, ttl=86400)  # 24 hours
```

---

## 📚 Related Files

- [`backend/retrievers/pubmed_retriever.py`](backend/retrievers/pubmed_retriever.py) - PubMed retriever implementation
- [`backend/retrievers/__init__.py`](backend/retrievers/__init__.py) - Retriever exports
- [`backend/agents/agent_controller.py`](backend/agents/agent_controller.py) - Integration with agent
- [`backend/config.py`](backend/config.py) - Configuration settings
- [`scripts/download_pubmed.py`](scripts/download_pubmed.py) - Bulk download script (optional)

---

## 🎉 Summary

### What You Just Gained:

✅ **30+ million medical articles** at your fingertips  
✅ **Real-time research access** (no downloads)  
✅ **Evidence-based citations** in every answer  
✅ **Automatic integration** with existing retrievers  
✅ **Minimal disk usage** (~0 MB)  
✅ **Configurable weights** for different use cases  

### Next Steps:

1. **Set your email**: `PUBMED_EMAIL=your@email.com`
2. **Restart backend**: `python scripts/run.py`
3. **Test a query**: "What are the treatments for diabetes?"
4. **Check sources**: Look for PubMed citations
5. **Adjust weights**: Based on your use case

**Your Medical RAG system now provides research-backed, evidence-based answers!** 🚀
