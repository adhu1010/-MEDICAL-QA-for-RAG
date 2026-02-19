# API Keys Configuration Guide

## 🔑 Where to Add API Keys

### **Step 1: Create `.env` File**

In the project root directory (`medical-rag-qa/`), create a file named `.env`:

```bash
# Copy the example file
cp .env.example .env

# Or create manually
# On Windows:
copy .env.example .env
```

### **Step 2: Add Your API Keys**

Edit the `.env` file and add your API keys:

---

## 📋 Available API Keys

### 1. **OpenAI API Key** (Optional)

**Used for**: GPT-based answer generation (alternative to BioGPT)

**Get it from**: https://platform.openai.com/api-keys

**Add to `.env`**:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note**: You already have BioGPT installed, so this is **optional** unless you want to use GPT-4 instead.

---

### 2. **HuggingFace API Key** (Optional)

**Used for**: Faster model downloads, access to gated models

**Get it from**: https://huggingface.co/settings/tokens

**Add to `.env`**:
```bash
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note**: Optional - models download without it, but may be slower.

---

### 3. **UMLS API Key** (For Enterprise Knowledge Graph)

**Used for**: Accessing full UMLS medical knowledge graph (4M+ concepts)

**Get it from**: 
1. Create account: https://uts.nlm.nih.gov/uts/signup-login
2. Accept license agreement
3. Get API key from: https://uts.nlm.nih.gov/uts/profile

**Add to `.env`**:
```bash
UMLS_ENABLED=true
UMLS_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
UMLS_VERSION=2024AA
```

**Benefits**: Access to comprehensive medical terminology and relationships.

---

### 4. **PubMed/NCBI API Key** (For Literature Access)

**Used for**: Accessing PubMed research articles (higher rate limits)

**Get it from**:
1. Create NCBI account: https://www.ncbi.nlm.nih.gov/account/
2. Go to Settings → API Key Management
3. Create new API key

**Add to `.env`**:
```bash
PUBMED_ENABLED=true
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Without API key**: 3 requests/second  
**With API key**: 10 requests/second

**Note**: Email is required even without API key.

---

### 5. **Neo4j Password** (For Persistent Graph Database)

**Used for**: Storing knowledge graph persistently

**Setup**:
1. Install Neo4j: https://neo4j.com/download/
2. Create database with password
3. Default URI: `bolt://localhost:7687`

**Add to `.env`**:
```bash
NEO4J_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=medical-kg
```

**Note**: Using NetworkX (in-memory) by default, Neo4j is optional.

---

## 📝 Complete `.env` File Example

Here's a complete example with all optional features:

```bash
# ============================================================================
# MEDICAL RAG QA SYSTEM - CONFIGURATION
# ============================================================================

# -------------------------
# LLM API Keys (Optional)
# -------------------------
# OpenAI (for GPT-4, optional - you have BioGPT)
OPENAI_API_KEY=sk-proj-your-key-here

# HuggingFace (optional - faster downloads)
HUGGINGFACE_API_KEY=hf_your-key-here

# -------------------------
# Medical Data APIs
# -------------------------
# UMLS Knowledge Graph (optional - for enterprise)
UMLS_ENABLED=false
UMLS_API_KEY=your-umls-key-here
UMLS_VERSION=2024AA
UMLS_SUBSET=snomed_rxnorm

# PubMed Literature (recommended - you already have this set up!)
PUBMED_ENABLED=true
PUBMED_MODE=api
PUBMED_EMAIL=your.email@example.com
PUBMED_API_KEY=your-ncbi-key-here  # Optional, for 10 req/sec instead of 3

# -------------------------
# Graph Database (Optional)
# -------------------------
# Neo4j (optional - using NetworkX by default)
NEO4J_ENABLED=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=medical-kg

# -------------------------
# Vector Store Settings
# -------------------------
VECTOR_STORE_PATH=./vector_store
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2

# -------------------------
# LLM Configuration
# -------------------------
# Using BioGPT-Large (already downloaded)
LLM_MODEL=microsoft/BioGPT-Large
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=512

# -------------------------
# Application Settings
# -------------------------
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG_MODE=true

# -------------------------
# Data Paths
# -------------------------
DATA_DIR=./data
MEDQUAD_PATH=./data/medquad
PUBMED_PATH=./data/pubmed
UMLS_PATH=./data/umls

# -------------------------
# Retrieval Settings
# -------------------------
TOP_K_VECTOR=5
TOP_K_KG=3
SIMILARITY_THRESHOLD=0.5

# -------------------------
# Safety Settings
# -------------------------
ENABLE_SAFETY_REFLECTION=true
ENABLE_CONTENT_FILTER=true

# -------------------------
# Logging
# -------------------------
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

---

## 🎯 Minimal Configuration (What You Need Right Now)

For your current setup, you **don't need any API keys** to get started!

Your `.env` file can be minimal:

```bash
# Minimal .env - Everything works without API keys!

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG_MODE=true

# LLM (using local BioGPT - already downloaded)
LLM_MODEL=microsoft/BioGPT-Large

# Data paths
DATA_DIR=./data

# That's it! No API keys required.
```

**Why?**
- ✅ BioGPT is local (no OpenAI key needed)
- ✅ MedQuAD data is local (already processed)
- ✅ NetworkX KG is local (no Neo4j needed)
- ✅ BioBERT embeddings are local (no HuggingFace key needed)

---

## 🚀 Quick Setup Instructions

### Option 1: No API Keys (Recommended to Start)

```bash
# Create minimal .env
echo "APP_PORT=8000" > .env
echo "LLM_MODEL=microsoft/BioGPT-Large" >> .env
echo "DEBUG_MODE=true" >> .env

# Start system
python scripts/run.py
```

### Option 2: With PubMed API (For Literature)

If you want real-time PubMed access:

```bash
# Create .env with PubMed
echo "PUBMED_EMAIL=your.email@example.com" > .env
echo "PUBMED_ENABLED=true" >> .env
echo "APP_PORT=8000" >> .env
```

### Option 3: Full Enterprise (All Features)

```bash
# Copy example and edit
cp .env.example .env

# Then edit .env and add:
# - UMLS_API_KEY (if you have it)
# - PUBMED_EMAIL (recommended)
# - NEO4J_PASSWORD (if using Neo4j)
```

---

## 📍 File Location

```
medical-rag-qa/
├── .env                    ← Create this file here
├── .env.example           ← Template (already exists)
├── backend/
├── frontend/
├── scripts/
└── README.md
```

**Important**: The `.env` file should be in the **root directory**, same level as `backend/` and `scripts/`.

---

## 🔒 Security Best Practices

### ✅ DO:
- ✅ Keep `.env` in `.gitignore` (already done)
- ✅ Never commit API keys to git
- ✅ Use environment-specific `.env` files
- ✅ Rotate API keys regularly
- ✅ Use `.env.example` as template

### ❌ DON'T:
- ❌ Commit `.env` to git
- ❌ Share API keys publicly
- ❌ Hardcode keys in source code
- ❌ Use production keys in development

---

## 🧪 Testing Configuration

### Check if .env is loaded:

```python
# Test script
from backend.config import settings

print(f"App Port: {settings.app_port}")
print(f"LLM Model: {settings.llm_model}")
print(f"Debug Mode: {settings.debug_mode}")
```

### Verify API keys (without exposing them):

```python
from backend.config import settings

# Check if keys are set (shows True/False, not actual keys)
print(f"OpenAI key set: {bool(settings.openai_api_key)}")
print(f"UMLS key set: {bool(getattr(settings, 'umls_api_key', None))}")
```

---

## 🆘 Troubleshooting

### Error: "Environment variable not found"

**Solution**: Make sure `.env` file exists in project root

```bash
# Check if .env exists
ls .env

# If not, create it
cp .env.example .env
```

### Error: "Invalid API key"

**For OpenAI**:
- Check key starts with `sk-`
- Verify at: https://platform.openai.com/api-keys

**For UMLS**:
- Check key format (UUID-like)
- Verify at: https://uts.nlm.nih.gov/uts/profile

**For PubMed**:
- Check email is valid
- API key is optional (works without it)

### System works without API keys?

**Yes!** Your current setup doesn't require any:
- ✅ BioGPT: Local model
- ✅ MedQuAD: Local data  
- ✅ BioBERT: Local embeddings
- ✅ NetworkX: In-memory graph

API keys are only needed for:
- OpenAI (if you want GPT-4)
- UMLS (if you want full medical ontology)
- PubMed API key (if you want faster rate limits)
- Neo4j (if you want persistent graph)

---

## 📊 API Key Priority

### Required (None!)
- Your system works without any API keys ✅

### Recommended:
1. **PubMed Email** - Free, enables literature access
   - Get: Just use your email
   - Benefit: Access to 30M+ research papers

### Optional:
2. **UMLS API Key** - Free, requires registration
   - Get: https://uts.nlm.nih.gov/uts/signup-login
   - Benefit: 4M+ medical concepts

3. **PubMed API Key** - Free, faster rate limits
   - Get: https://www.ncbi.nlm.nih.gov/account/
   - Benefit: 10 req/sec vs 3 req/sec

### Enterprise:
4. **OpenAI API Key** - Paid, for GPT-4
   - Get: https://platform.openai.com/
   - Benefit: More powerful than BioGPT

5. **Neo4j** - Free (community) or paid (enterprise)
   - Get: https://neo4j.com/
   - Benefit: Persistent graph storage

---

## ✅ Summary

**Where to add API keys**: Create `.env` file in project root

**What you need right now**: **Nothing!** System works without API keys.

**Optional additions**:
- PubMed email (free, recommended)
- UMLS API key (free, for enterprise features)

**File to create**:
```bash
medical-rag-qa/.env
```

**Minimal content**:
```bash
APP_PORT=8000
LLM_MODEL=microsoft/BioGPT-Large
```

You're ready to go! 🚀