# 🪟 Windows Installation Guide

## The Problem

You're seeing this error because some packages (like `spacy` and `scispacy`) require C++ compilation on Windows, which can fail if you don't have the right build tools.

```
ERROR: Failed building wheel for blis
```

## ✅ Quick Solution (Recommended)

### Option 1: Minimal Installation (Works on all systems)

```bash
# Use the minimal requirements that avoid problematic packages
python -m pip install -r requirements-minimal.txt
```

This installs only essential packages and the system will work with basic functionality.

### Option 2: Install Core Packages Manually

```bash
# Install essential packages one by one
pip install fastapi uvicorn pydantic python-multipart
pip install transformers torch --index-url https://download.pytorch.org/whl/cpu
pip install chromadb sentence-transformers
pip install networkx pandas numpy requests
pip install python-dotenv loguru tqdm
```

## 🔧 Full Installation (If you want advanced NLP)

### Step 1: Install Build Tools

If you want the full installation with medical NLP, you need build tools:

**Option A: Visual Studio Build Tools (Recommended)**
1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "C++ build tools" workload
3. Restart your computer

**Option B: Conda (Alternative)**
```bash
# Install Anaconda/Miniconda first
conda install -c conda-forge spacy
conda install -c conda-forge transformers
pip install scispacy
```

### Step 2: Install spaCy Models

```bash
# After spaCy is installed
python -m spacy download en_core_web_sm
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz
```

## ✨ What Works with Minimal Installation?

The minimal installation still gives you:

✅ **Full API functionality**
- All FastAPI endpoints work
- Web interface works
- Health checks work

✅ **Core RAG pipeline**
- Vector retrieval (ChromaDB + Sentence Transformers)
- Knowledge graph (NetworkX)
- Answer generation (local models or OpenAI)
- Safety validation

✅ **Basic entity extraction**
- Simple regex-based medical term detection
- Works for common drugs (Metformin, Amoxicillin)
- Works for common conditions (diabetes, hypertension)

⚠️ **What's missing with minimal installation:**
- Advanced medical NER (scispaCy)
- UMLS concept mapping
- Some evaluation metrics

## 🚀 Test Your Installation

After installation, test it:

```bash
# Test the system
python scripts/test_pipeline.py

# If that works, run the server
python scripts/run.py

# Then try asking a question!
```

## 📝 Updating Configuration

If using minimal installation, edit `.env`:

```bash
# Use simpler models that don't require advanced NLP
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=microsoft/DialoGPT-medium

# Disable advanced features
ENABLE_UMLS_LINKING=False
```

## 🆘 Still Having Issues?

### Common Windows Issues:

**Error: "Microsoft Visual C++ 14.0 is required"**
- Install Visual Studio Build Tools (see Step 1 above)

**Error: "Failed building wheel for torch"**
- Use CPU-only torch: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

**Error: "Access is denied"**
- Run PowerShell as Administrator
- Or use `--user` flag: `pip install --user -r requirements.txt`

**Error: "No module named 'distutils'"**
- Update Python: Download latest from python.org
- Or: `pip install setuptools`

### Alternative: Use Docker

If all else fails, use Docker:

```bash
# Install Docker Desktop for Windows
# Then run:
docker-compose up --build
```

## 🎯 Quick Commands for Windows

```bash
# Complete minimal setup (copy-paste this)
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pydantic python-multipart
python -m pip install transformers torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install chromadb sentence-transformers networkx
python -m pip install pandas numpy requests python-dotenv loguru
python scripts/download_data.py
python scripts/build_vector_store.py
python scripts/build_knowledge_graph.py
python scripts/run.py
```

## ✅ Success Criteria

You know it's working when:

1. ✅ `python scripts/test_pipeline.py` runs without errors
2. ✅ `python scripts/run.py` starts the server
3. ✅ You can open http://localhost:8000/docs
4. ✅ You can ask "What is diabetes?" and get an answer

## 💡 Pro Tips for Windows

1. **Use Windows Terminal** instead of Command Prompt
2. **Install Python from python.org** (not Microsoft Store)
3. **Use virtual environments**: `python -m venv venv`
4. **Update pip first**: `python -m pip install --upgrade pip`
5. **If stuck, try WSL** (Windows Subsystem for Linux)

---

**Bottom line:** The minimal installation gets you 90% of the functionality without the headaches. You can always add advanced features later!