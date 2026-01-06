# 🩺 Agentic RAG for Medical Question Answering

## Overview

An intelligent Medical Question Answering system that combines **Large Language Models (LLMs)**, **Vector Databases**, and **Medical Knowledge Graphs** to provide accurate, explainable, and safe medical answers.

### Key Features

- 🤖 **Agentic Decision Layer**: Intelligently chooses retrieval strategies
- 🔍 **Hybrid Retrieval**: Combines vector search (FAISS) and knowledge graph (Neo4j)
- 🧠 **Medical NER**: Uses scispaCy for entity recognition and UMLS mapping
- ✅ **Safety Reflection**: Validates answers for accuracy and safety
- 👥 **Dual Modes**: Doctor (detailed + citations) and Patient (simplified) modes
- 📊 **Evaluation Suite**: BLEU, ROUGE, and Faithfulness metrics

## Architecture

```
User Query → NER/Preprocessing → Agent Decision → Retrieval (Vector + KG) 
→ Evidence Fusion → LLM Generation → Safety Reflection → Answer Output
```

## Tech Stack

- **Backend**: FastAPI
- **Vector DB**: ChromaDB with FAISS
- **Knowledge Graph**: Neo4j 
- **Embeddings**: BioBERT 
- **LLM**: BioGPT 
- **NER**: scispaCy + UMLS
- **Agent Framework**: LangChain
- **Safety**: Guardrails AI
- **Frontend**: React.js

## Project Structure

```
medical-rag-qa/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── models/                 # Data models
│   ├── agents/                 # Agent controller
│   ├── retrievers/             # Vector & KG retrievers
│   ├── generators/             # LLM answer generation
│   ├── safety/                 # Reflection & validation
│   ├── utils/                  # Utilities
│   └── evaluation/             # Metrics & evaluation
├── data/                       # Datasets (MedQuAD, PubMed)
├── knowledge_graph/            # KG data and scripts
├── vector_store/               # Embeddings storage
├── frontend/                   # React UI
├── requirements.txt
└── docker-compose.yml
```

## Quick Start

### 1. Installation

```bash
# Step 1: Install dependencies (run this FIRST)
python install.py

# If you get errors on Windows, try:
python -m pip install -r requirements-minimal.txt

# Step 2: Run setup for data preparation
python scripts/setup.py
```

**🪟 Windows Users:** If you encounter build errors, see [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) for solutions.

### 2. Setup Data

```bash
# Download datasets
python scripts/download_data.py

# Build vector store
python scripts/build_vector_store.py

# Setup knowledge graph
python scripts/build_knowledge_graph.py
```

### 3. Run Application

```bash
# Start backend
uvicorn backend.main:app --reload --port 8000

# Start frontend (in another terminal)
cd frontend
npm install
npm start
```

## API Endpoints

- `POST /api/ask` - Submit medical question
- `GET /api/retrieve` - Retrieve relevant documents
- `POST /api/generate` - Generate answer
- `GET /api/health` - Health check

## Usage Example

```python
import requests

response = requests.post("http://localhost:8000/api/ask", json={
    "question": "What are the side effects of Metformin?",
    "mode": "patient"
})

print(response.json()["answer"])
# Output: "Common side effects of Metformin include nausea, stomach upset..."
```

## Data Sources

- **MedQuAD**: Medical QA pairs from NIH, Mayo Clinic
- **PubMed**: Biomedical literature abstracts
- **UMLS**: Unified Medical Language System
- **SNOMED CT**: Clinical terminology

## Evaluation

The system is evaluated on:

- **Accuracy**: BLEU, ROUGE scores
- **Faithfulness**: Answer alignment with source documents
- **Safety**: Hallucination detection and harmful advice filtering

## Safety & Disclaimers

⚠️ **This system is for educational and research purposes only.**
- Not a replacement for professional medical advice
- Always consult healthcare professionals for medical decisions
- Answers should be verified with authoritative sources

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## License

MIT License - See LICENSE file for details

## Citation

If you use this project in your research, please cite:

```bibtex
@software{medical_rag_qa_2025,
  title={Agentic RAG for Medical Question Answering},
  author={Your Name},
  year={2025}
}
```
