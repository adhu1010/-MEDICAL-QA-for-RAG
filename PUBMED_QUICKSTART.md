# PubMed API Quick Start Guide

## ⚡ 3-Minute Setup

### Step 1: Set Your Email (Required)

**Option A: Environment Variable** (PowerShell)
```powershell
$env:PUBMED_EMAIL="your.email@example.com"
```

**Option B: .env File** (Recommended)
```bash
# Create or edit .env file
echo PUBMED_EMAIL=your.email@example.com >> .env
```

### Step 2: Optional - Get API Key (Recommended)

**Why?** Increases rate limit from 3 req/s to 10 req/s (3x faster!)

1. Visit: https://www.ncbi.nlm.nih.gov/account/
2. Create free account or login
3. Go to **Settings → API Key Management**
4. Create new API key
5. Add to `.env`:

```bash
PUBMED_API_KEY=your-api-key-here
```

### Step 3: Test Integration

```bash
python scripts/test_pubmed_api.py
```

**Expected output**:
```
✅ PubMed configuration valid!
✅ Found 100 articles
✅ Retrieved 3 evidences
```

### Step 4: Start Backend

```bash
python scripts/run.py
```

### Step 5: Test a Query

Open frontend and ask:
> "What are the treatments for diabetes?"

**Look for PubMed citations** in the sources section!

---

## 🎯 What You Get

✅ **30+ million medical articles** from PubMed  
✅ **Real-time research access** (no downloads)  
✅ **5 citations per answer** from peer-reviewed journals  
✅ **Zero storage** (~0 MB)  
✅ **Evidence-based answers** with research backing  

---

## ⚙️ Configuration

### Complete `.env` Example

```bash
# ============================================
# PUBMED API CONFIGURATION
# ============================================
PUBMED_ENABLED=true
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=your-ncbi-api-key-here  # Optional
PUBMED_MAX_RESULTS=5

# Other retrievers
TOP_K_VECTOR=5
TOP_K_KG=3
TOP_K_PUBMED=5
```

### Adjust Weights (Optional)

Edit [`backend/config.py`](backend/config.py):

```python
class AgentConfig:
    # For research-focused answers (increase PubMed weight)
    FUSION_WEIGHT_KG = 0.3
    FUSION_WEIGHT_VECTOR = 0.2
    FUSION_WEIGHT_PUBMED = 0.35  # Higher for research
    FUSION_WEIGHT_SPARSE = 0.15
    
    # For patient education (decrease PubMed weight)
    FUSION_WEIGHT_KG = 0.4
    FUSION_WEIGHT_VECTOR = 0.3
    FUSION_WEIGHT_PUBMED = 0.1   # Lower for simpler answers
    FUSION_WEIGHT_SPARSE = 0.2
```

---

## 🔍 Verify It's Working

### Check Logs

When backend starts:
```
INFO | PubMed retriever initialized (email=your@email.com, rate=10 req/s)
```

### Check Query Response

Sources should include:
```json
{
  "sources": [
    "PubMed: Smith AB et al. Diabetes Care. 2023. [PMID: 32456789]",
    "PubMed: Johnson CD et al. BMJ. 2024. [PMID: 33567890]",
    "KG: Metformin TREATS Type2Diabetes",
    "MedQuAD: Diabetes FAQ"
  ]
}
```

---

## 🚨 Troubleshooting

### "PubMed retriever disabled"

**Cause**: No email set

**Fix**:
```bash
$env:PUBMED_EMAIL="your@email.com"  # PowerShell
# OR
echo PUBMED_EMAIL=your@email.com >> .env
```

### "HTTP Error 429: Too Many Requests"

**Cause**: Rate limit exceeded (3 req/s without API key)

**Fix**: Get NCBI API key (see Step 2)

### "No PubMed articles found"

**Causes**:
1. Query too specific
2. No matches in PubMed
3. Entity extraction failed

**Debug**:
```bash
python scripts/test_pubmed_api.py
```

---

## 📚 Full Documentation

For detailed information:
- [`PUBMED_DYNAMIC_INTEGRATION.md`](PUBMED_DYNAMIC_INTEGRATION.md) - Complete guide
- [`backend/retrievers/pubmed_retriever.py`](backend/retrievers/pubmed_retriever.py) - Implementation
- [`scripts/test_pubmed_api.py`](scripts/test_pubmed_api.py) - Test suite

---

## 🎉 Success!

Your Medical RAG system now provides **research-backed, evidence-based answers** from 30+ million PubMed articles!

**Try it now**: Ask "What are the side effects of aspirin?" and check the sources! 🚀
