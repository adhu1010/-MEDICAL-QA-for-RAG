# 🚀 Setup Guide - Medical RAG QA System

## Prerequisites

- Python 3.9 or higher
- pip package manager
- 8GB+ RAM recommended
- (Optional) CUDA-capable GPU for faster inference
- (Optional) Neo4j for persistent knowledge graph

## Installation Methods

### Method 1: Automated Setup (Recommended)

```bash
# 1. Clone or download the project
cd medical-rag-qa

# 2. Run the automated setup script
python scripts/setup.py
```

This will guide you through:
- Installing dependencies
- Downloading medical NLP models
- Creating configuration files
- Preparing sample data
- Building vector store and knowledge graph

### Method 2: Manual Setup

#### Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Download scispaCy Model

```bash
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz
```

#### Step 4: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# Add API keys if using OpenAI or other services
```

#### Step 5: Prepare Data

```bash
# Download sample medical data
python scripts/download_data.py

# Build vector store
python scripts/build_vector_store.py

# Build knowledge graph
python scripts/build_knowledge_graph.py
```

## Configuration

### Environment Variables (.env file)

```bash
# API Keys (optional - for advanced LLM features)
OPENAI_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Neo4j (optional - if using persistent graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Model Settings
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2
LLM_MODEL=microsoft/BioGPT-Large

# Application Settings
DEBUG_MODE=True
LOG_LEVEL=INFO
```

## Running the System

### Option 1: Quick Start

```bash
python scripts/run.py
```

This starts the backend server at http://localhost:8000

### Option 2: Manual Start

```bash
# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, serve frontend (optional)
python -m http.server 3000 --directory frontend
```

### Option 3: Docker (Advanced)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - Neo4j: http://localhost:7474
```

## Testing the Installation

### 1. Test the Pipeline

```bash
python scripts/test_pipeline.py
```

This will:
- Initialize all components
- Process sample medical questions
- Retrieve evidence
- Generate answers
- Validate safety

### 2. Test the API

Visit http://localhost:8000/docs to access the interactive API documentation.

Try a sample request:

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the side effects of Metformin?",
    "mode": "patient"
  }'
```

### 3. Test the Frontend

Open `frontend/index.html` in your browser or visit http://localhost:3000

## Troubleshooting

### Issue: Import errors

**Solution:**
```bash
# Ensure you're in the project root directory
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: scispaCy model not found

**Solution:**
```bash
# Download the model explicitly
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz
```

### Issue: ChromaDB errors

**Solution:**
```bash
# Clear vector store and rebuild
rm -rf vector_store/
python scripts/build_vector_store.py
```

### Issue: Out of memory

**Solution:**
- Use smaller models (e.g., `all-MiniLM-L6-v2` for embeddings)
- Reduce `TOP_K_VECTOR` in config
- Process fewer documents at a time

### Issue: API connection refused

**Solution:**
```bash
# Check if server is running
curl http://localhost:8000/api/health

# Check firewall settings
# Ensure port 8000 is not blocked
```

## Using Production Data

The sample data is for demonstration only. For production:

### 1. MedQuAD Dataset

```bash
git clone https://github.com/abachaa/MedQuAD.git data/medquad_full
```

### 2. PubMed Data

Use the NCBI E-utilities API:

```python
from Bio import Entrez
Entrez.email = "your_email@example.com"
# Download abstracts for specific topics
```

### 3. UMLS Knowledge

1. Register at https://uts.nlm.nih.gov/uts/
2. Download UMLS Metathesaurus
3. Load into Neo4j or process with scripts

## Advanced Configuration

### Using Neo4j

1. Install Neo4j Desktop or use Docker:
```bash
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.12
```

2. Update `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

3. In `backend/retrievers/kg_retriever.py`, set `use_neo4j=True`

### Using OpenAI API

1. Get API key from https://platform.openai.com/

2. Update `.env`:
```bash
OPENAI_API_KEY=sk-...
```

3. In `backend/generators/answer_generator.py`, use `model_type="openai"`

## Next Steps

- ✅ Setup complete? → Read [README.md](README.md) for usage
- 🧪 Want to test? → Run `python scripts/test_pipeline.py`
- 📚 Want to learn more? → Check API docs at `/docs`
- 🔧 Want to customize? → See architecture documentation

## Support

For issues or questions:
- Check [README.md](README.md)
- Review error logs in `logs/app.log`
- Examine API documentation at http://localhost:8000/docs

## Security Notes

⚠️ **Important:**
- Do NOT commit `.env` file to version control
- Keep API keys secure
- This is for research/education only
- Not for production medical use without proper validation
