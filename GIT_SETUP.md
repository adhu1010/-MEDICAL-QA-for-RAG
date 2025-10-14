# Git Setup Guide - Enterprise Medical RAG QA

## 🎯 What to Commit

This guide helps you add the enterprise setup to git while excluding large data files.

---

## 📋 Files to Include in Git

### ✅ Code and Scripts (COMMIT)
```
scripts/
├── enterprise_setup.py          # Interactive enterprise setup wizard
├── download_umls.py             # UMLS knowledge graph downloader
├── download_pubmed.py           # PubMed literature API integration
├── process_medquad.py           # MedQuAD data processor
├── build_vector_store.py        # Updated to use real data
├── build_knowledge_graph.py     # Updated for Disease Ontology
├── download_data.py             # Original sample data generator
├── run.py                       # Backend runner
├── setup.py                     # Project setup
└── test_*.py                    # Test scripts
```

### ✅ Documentation (COMMIT)
```
*.md files:
├── ENTERPRISE_SETUP.md          # Comprehensive enterprise guide
├── ENTERPRISE_OPTIONS.md        # Configuration decision helper
├── SETUP_PROGRESS.md            # Current setup progress tracker
├── GIT_SETUP.md                 # This file
├── BIOGPT_SETUP.md              # BioGPT installation guide
├── HOW_SEARCH_WORKS.md          # Semantic search explanation
├── CURRENT_STATUS.md            # System status
├── FIXES_APPLIED.md             # Bug fix documentation
├── README.md                    # Main readme
├── ARCHITECTURE.md              # System architecture
├── API_DOCUMENTATION.md         # API docs
├── GETTING_STARTED.md           # Quick start
└── TROUBLESHOOTING.md           # Troubleshooting guide
```

### ✅ Configuration (COMMIT)
```
.env.example                     # Template (NOT .env with real keys!)
.gitignore                       # Updated to exclude large files
requirements.txt                 # Python dependencies
requirements-minimal.txt         # Minimal dependencies
config/                          # Config files (if any)
```

### ✅ Backend Code (COMMIT)
```
backend/
├── __init__.py
├── config.py                    # Configuration settings
├── main.py                      # FastAPI application
├── agents/                      # Agentic controller
├── generators/                  # Answer generation
├── preprocessing/               # Query processing
├── retrievers/                  # Vector & KG retrievers
└── safety/                      # Safety validation
```

### ✅ Frontend (COMMIT)
```
frontend/
├── index.html                   # Web interface
└── styles.css                   # Styling
```

---

## ❌ Files to EXCLUDE from Git

### Large Data Files (DO NOT COMMIT)
```
data/
├── MedQuAD-master/              # ~50MB, downloaded separately
├── medquad_processed.json       # ~30MB, generated from MedQuAD
├── disease_ontology.obo         # ~6MB, downloaded from GitHub
├── disease_ontology_processed.json  # ~20MB, generated
└── enterprise/                  # UMLS/PubMed data (GB size)
```

### Vector Store (DO NOT COMMIT)
```
vector_store/                    # Generated from data (500MB-2GB)
├── chroma.sqlite3
└── *.parquet
```

### Model Cache (DO NOT COMMIT)
```
models/                          # HuggingFace models (6GB+ for BioGPT)
.cache/huggingface/
transformers_cache/
```

### Sensitive Files (DO NOT COMMIT)
```
.env                             # Contains API keys/passwords
.env.enterprise                  # Enterprise credentials
*_api_key.txt
*_password.txt
```

### Temporary Files (DO NOT COMMIT)
```
__pycache__/
*.pyc
logs/
.pytest_cache/
```

---

## 🚀 Git Commands to Add Enterprise Features

### Step 1: Check Status
```bash
cd "c:\Users\eahkf\AppData\Roaming\Qoder\User\globalStorage\alefragnani.project-manager\medical-rag-qa"
git status
```

This shows what files are new/modified.

### Step 2: Add New Enterprise Scripts
```bash
# Add enterprise setup scripts
git add scripts/enterprise_setup.py
git add scripts/download_umls.py
git add scripts/download_pubmed.py
git add scripts/process_medquad.py

# Add updated build scripts
git add scripts/build_vector_store.py
git add scripts/build_knowledge_graph.py

# Add documentation
git add ENTERPRISE_SETUP.md
git add ENTERPRISE_OPTIONS.md
git add SETUP_PROGRESS.md
git add GIT_SETUP.md

# Add updated gitignore
git add .gitignore
```

### Step 3: Commit with Descriptive Message
```bash
git commit -m "feat: Add enterprise setup for UMLS, PubMed, and Neo4j integration

- Add interactive enterprise setup wizard (enterprise_setup.py)
- Add UMLS knowledge graph downloader with API integration
- Add PubMed literature API integration
- Add MedQuAD processing for 16K+ real medical QA pairs
- Update vector store builder to use full MedQuAD dataset
- Update knowledge graph builder to use Disease Ontology
- Add comprehensive enterprise documentation
- Update .gitignore to exclude large data files (MedQuAD, embeddings, models)

System now supports:
- 16,407 medical QA pairs from MedQuAD
- 14,460 diseases from Disease Ontology
- Optional UMLS integration (4M+ concepts)
- Optional PubMed API access (7M+ articles)
- Optional Neo4j persistent storage
"
```

### Step 4: Push to Remote (if you have one)
```bash
git push origin main
# or
git push origin master
```

---

## 📝 Alternative: Add All Code Files at Once

If you want to add all code and docs in one go:

```bash
# Stage all new/modified files (excluding gitignored ones)
git add .

# Review what will be committed
git status

# Commit
git commit -m "feat: Add enterprise medical RAG setup with UMLS/PubMed/Neo4j support"

# Push
git push
```

---

## 🔍 Verify What Will Be Committed

Before committing, verify you're NOT accidentally committing large files:

```bash
# See what's staged
git status

# See file sizes
git ls-files --stage | awk '{print $2, $4}' | while read hash file; do 
    size=$(git cat-file -s $hash 2>/dev/null || echo 0)
    if [ $size -gt 1000000 ]; then 
        echo "Large file: $file ($size bytes)"
    fi
done
```

**Warning**: If you see files > 50MB, check if they should be in `.gitignore`.

---

## 📦 Create Data Download Instructions

Since data files aren't in git, create instructions for others:

**Already created**: `ENTERPRISE_SETUP.md` includes full download instructions!

Users will:
1. Clone your repo (gets code only)
2. Follow `ENTERPRISE_SETUP.md` to download data
3. Run setup scripts to build system

---

## 🎯 Recommended Commit Strategy

### Option 1: Single Commit (Quick)
```bash
git add .
git commit -m "feat: Add enterprise medical RAG setup"
git push
```

### Option 2: Organized Commits (Better)
```bash
# Commit 1: Core enterprise scripts
git add scripts/enterprise_setup.py scripts/download_umls.py scripts/download_pubmed.py
git commit -m "feat: Add enterprise setup wizard and data downloaders"

# Commit 2: Data processing
git add scripts/process_medquad.py
git commit -m "feat: Add MedQuAD processor for 16K+ medical QA pairs"

# Commit 3: Updated build scripts
git add scripts/build_vector_store.py scripts/build_knowledge_graph.py
git commit -m "feat: Update builders to use real medical datasets"

# Commit 4: Documentation
git add *.md
git commit -m "docs: Add comprehensive enterprise setup documentation"

# Commit 5: Config
git add .gitignore
git commit -m "chore: Update gitignore to exclude large data files"

# Push all
git push
```

---

## ⚠️ Important Notes

### DO NOT Commit:
- ❌ API keys (UMLS, PubMed)
- ❌ Passwords (Neo4j)
- ❌ Downloaded datasets (MedQuAD, Disease Ontology)
- ❌ Generated files (vector_store/, processed JSON)
- ❌ HuggingFace model cache (6GB+)

### DO Commit:
- ✅ All `.py` scripts
- ✅ All `.md` documentation
- ✅ `.env.example` (template only)
- ✅ `requirements.txt`
- ✅ `.gitignore`

---

## 🔒 Security Check

Before pushing, verify no secrets are committed:

```bash
# Search for common secret patterns
git grep -E "api_key|password|secret|token" -- '*.py' '*.md' '*.txt'

# If you find real credentials, remove them!
```

---

## 📊 What Your Repository Will Contain

After committing:

```
medical-rag-qa/
├── 📁 scripts/              ← All setup and build scripts ✅
├── 📁 backend/              ← Backend application code ✅
├── 📁 frontend/             ← Web interface ✅
├── 📁 config/               ← Configuration files ✅
├── 📄 *.md                  ← Documentation (15+ guides) ✅
├── 📄 requirements.txt      ← Dependencies ✅
├── 📄 .gitignore            ← Exclusion rules ✅
├── 📄 .env.example          ← Config template ✅
└── 📄 README.md             ← Main readme ✅

NOT in repo (downloaded separately):
├── 📁 data/                 ← 16K+ QA pairs (users download) ❌
├── 📁 vector_store/         ← Users build from data ❌
├── 📁 models/               ← HuggingFace downloads ❌
└── 📄 .env                  ← User's credentials ❌
```

---

## ✅ Quick Checklist

Before `git push`:

- [ ] Updated `.gitignore` to exclude data/models
- [ ] Removed any API keys/passwords from code
- [ ] Added `.env.example` (template only)
- [ ] Committed all scripts and documentation
- [ ] Tested that setup works from clean clone (optional)
- [ ] No files > 50MB in commit
- [ ] Documentation explains how to download data

---

## 🆘 If You Accidentally Committed Large Files

Remove large file from history:
```bash
# Remove specific file
git rm --cached data/medquad_processed.json
git commit -m "chore: Remove large data file from tracking"

# If already pushed, need to force push (CAREFUL!)
git push --force
```

Better: Just add to `.gitignore` going forward.

---

Ready to commit! Use the commands above based on your preferred strategy. The `.gitignore` is already updated to protect you from committing large files.
