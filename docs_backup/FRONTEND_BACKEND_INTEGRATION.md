# Frontend-Backend Integration Guide

## Overview

This document describes how the React frontend is integrated with the FastAPI backend for the Medical RAG QA System. The frontend now communicates with the backend API instead of using external services like Gemini API.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│                  (Vite + React 18 + Firebase)               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTP REST API (Fetch)
                 │
┌────────────────▼────────────────────────────────────────────┐
│                  FastAPI Backend                            │
│         (Medical RAG QA System)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • Query Preprocessing (NER, Entity Extraction)            │
│  • Agentic Orchestration (Intent Classification)           │
│  • Hybrid Retrieval (Vector Store + Knowledge Graph)       │
│  • LLM Answer Generation (BioGPT)                          │
│  • Safety Validation & Corrections                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Prerequisites

- Node.js 16+ (for frontend)
- Python 3.9+ (for backend)
- npm or yarn package manager

### 2. Backend Setup

```bash
cd medical-rag-qa/backend

# Install Python dependencies
pip install -r ../requirements.txt

# Configure environment variables
# Update ../.env with your API keys and settings
# Key variables:
# - OPENAI_API_KEY: For LLM capabilities
# - HUGGINGFACE_API_KEY: For embeddings
# - NEO4J_URI: Knowledge graph database connection
# - EMBEDDING_MODEL: biobert-base-cased-v1.2 (or similar)
# - LLM_MODEL: microsoft/BioGPT-Large (or alternative)

# Start the backend server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd medical-rag-qa/frontend

# Install Node dependencies
npm install

# Configure environment for backend connection
# The .env.local file is already configured with:
# VITE_API_BASE_URL=http://localhost:8000

# Start the frontend development server
npm run dev
```

The frontend will be available at `http://localhost:5173` (default Vite port)

### 4. Run Both Simultaneously (Recommended)

From the `medical-rag-qa` directory:

```bash
npm run dev:full
```

This uses `concurrently` to run both the frontend and backend servers at the same time.

## API Integration Details

### API Client (`frontend/src/api.js`)

The frontend uses a centralized API client class for all backend communication:

```javascript
import { apiClient } from './api';

// Ask a medical question
const response = await apiClient.askQuestion(
  'What are the side effects of aspirin?',
  'auto'  // mode: 'auto', 'patient', or 'doctor'
);

// Health check
const health = await apiClient.healthCheck();

// Preprocess a query (debug)
const processed = await apiClient.preprocessQuery(question);

// Get system statistics
const stats = await apiClient.getStats();
```

### Backend API Endpoints

#### 1. Health Check
```
GET /api/health
Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "preprocessor": "ready",
    "agent": "ready",
    "generator": "ready",
    "safety_reflector": "ready"
  }
}
```

#### 2. Ask Question (Main Endpoint)
```
POST /api/ask
Request:
{
  "question": "What is aspirin used for?",
  "mode": "auto"  // "auto", "patient", or "doctor"
}

Response:
{
  "question": "What is aspirin used for?",
  "answer": "Aspirin is commonly used...",
  "mode": "patient",
  "sources": [
    {
      "title": "Document Title",
      "content": "Source text...",
      "score": 0.95
    }
  ],
  "confidence": 0.87,
  "safety_validated": true,
  "metadata": {
    "retrieval_strategy": "hybrid",
    "entities_found": 5,
    "evidence_count": 3,
    "query_type": "factoid",
    "detected_mode": "patient"
  }
}
```

#### 3. Preprocess Query
```
POST /api/preprocess
Request:
{
  "question": "What is aspirin used for?",
  "mode": "auto"
}

Response:
{
  "original_question": "What is aspirin used for?",
  "entities": ["aspirin", "uses"],
  "detected_mode": "patient",
  "suggested_strategy": "hybrid",
  "query_type": "factoid"
}
```

#### 4. System Statistics
```
GET /api/stats
Response:
{
  "vector_store": {
    "collection_count": 5000,
    "embedding_dim": 768
  },
  "knowledge_graph": {
    "nodes": 12534,
    "edges": 45678
  }
}
```

## Frontend Components Integration

### Main App Component (`frontend/interface.jsx`)

The frontend has been updated to:

1. **Initialize Firebase** for persistent chat history and user management
2. **Call Backend API** via the API client instead of external LLM services
3. **Process Responses** and format them for UI display
4. **Handle Errors** with user-friendly error messages

Key changes:

```javascript
// Old: Used Gemini API directly
// const response = await fetch(`${GEMINI_API_URL}${API_KEY}`, {...})

// New: Uses backend API
const response = await apiClient.askQuestion(query, 'auto');
```

### Response Processing

The backend response is transformed to match the UI expectations:

```javascript
const structuredResponse = {
  text: response.answer,                          // Main answer text
  confidence: Math.round(response.confidence * 100),  // Confidence score
  persona: response.metadata?.detected_mode === 'patient' 
    ? 'Patient/General' 
    : 'Doctor/Clinical',                          // User persona
  mode: response.metadata?.retrieval_strategy,    // Retrieval method
  citation: response.sources?.map(...).join('\n'), // Source references
  safety_validated: response.safety_validated,    // Safety check result
};
```

### Message Storage

Messages are stored in Firestore with the following structure:

```
artifacts/{appId}/users/{userId}/chats/{chatId}/messages
├── User Message
│   ├── text: "What is aspirin?"
│   ├── role: "user"
│   └── timestamp: serverTimestamp()
└── Model Response
    ├── text: "{...JSON structured response...}"
    ├── role: "model"
    └── timestamp: serverTimestamp()
```

## Environment Configuration

### Frontend (`.env.local`)

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production, update to your backend server URL:
```env
VITE_API_BASE_URL=https://your-backend-domain.com
```

### Backend (`.env`)

Key configurations:

```env
# API Keys
OPENAI_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Server Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG_MODE=True

# CORS Settings (already allows frontend)
# Configured in backend/main.py with wildcard origins

# Vector Store & LLM
EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2
LLM_MODEL=microsoft/BioGPT-Large
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=512

# Data Paths
DATA_DIR=./data
MEDQUAD_PATH=./data/medquad

# Safety Settings
ENABLE_SAFETY_REFLECTION=True
ENABLE_CONTENT_FILTER=True
```

## CORS Configuration

The backend is configured to accept requests from all origins (frontend-friendly):

```python
# backend/main.py (lines 42-49)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict CORS to specific frontend URLs:

```python
allow_origins=[
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com",
]
```

## Data Flow: Question to Answer

```
1. User enters question in frontend
   ↓
2. Frontend calls: apiClient.askQuestion(question, mode)
   ↓
3. Backend receives POST /api/ask request
   ↓
4. Backend pipeline:
   a) Preprocess query (NER, entity extraction)
   b) Agent decides retrieval strategy (KG, Vector, Hybrid)
   c) Retrieve evidence from vector store and/or knowledge graph
   d) Generate answer using LLM
   e) Validate answer with safety reflector
   f) Apply corrections if needed
   ↓
5. Backend returns structured MedicalAnswer response
   ↓
6. Frontend processes and displays:
   - Main answer text
   - Confidence score
   - User persona
   - Retrieval method used
   - Source citations
   - Safety validation status
   ↓
7. Message saved to Firestore for chat history
```

## Testing the Integration

### 1. Check Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response: `{"status": "healthy", ...}`

### 2. Test API from Frontend Console

```javascript
// In browser developer console
await apiClient.healthCheck()
await apiClient.askQuestion("What is aspirin?", "auto")
await apiClient.getStats()
```

### 3. Full Integration Test

1. Start backend: `npm run backend:dev`
2. Start frontend: `npm run dev`
3. Open browser at `http://localhost:5173`
4. Ask a medical question
5. Verify response appears with confidence score and sources

## Troubleshooting

### Issue: "Unable to reach the backend API"

**Causes:**
- Backend is not running
- Frontend is configured with wrong backend URL
- CORS headers are blocked

**Solutions:**
1. Ensure backend is running: `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. Check `.env.local` has correct `VITE_API_BASE_URL`
3. Check browser console for CORS errors
4. Verify firewall allows port 8000

### Issue: Slow responses

**Causes:**
- Large batch of documents being processed
- Vector embeddings taking time
- LLM inference latency

**Solutions:**
1. Check backend logs for processing time
2. Reduce `TOP_K_VECTOR` in `.env` if set too high
3. Use `requirements-minimal.txt` for faster setup

### Issue: "Firebase not configured"

**Causes:**
- Firebase config missing in `index.html`
- Firebase auth not initialized

**Solutions:**
1. Ensure `index.html` has Firebase config in global variables
2. Check Firebase project settings match `index.html`
3. Verify Firestore database is created

## Performance Optimization

### Frontend
- Messages are lazy-loaded via Firestore real-time listeners
- Sidebar chat history auto-scrolls to latest messages
- UI updates only when data changes (React optimization)

### Backend
- Vector store uses approximate nearest neighbor search (ANN)
- Knowledge graph queries use indexed Cypher patterns
- Answer generation uses model caching where available
- Safety validation is parallelized where possible

## Security Considerations

### Frontend
- Firebase anonymously signs in users (secure by default)
- Sensitive data stored only in Firestore with security rules
- No API keys exposed in frontend code

### Backend
- CORS restricted in production to known domains
- Input validation on all API endpoints
- SQL injection prevention via ORM queries
- Rate limiting recommended for production (not implemented)

### Data Privacy
- Chat history stored per user in Firestore
- Queries logged only in backend logs (no persistent storage of queries)
- Models do not store user data between requests

## Production Deployment

### Frontend (Vite)
```bash
npm run build
# Outputs to dist/ folder
# Deploy to Vercel, Netlify, or your web server
```

### Backend (FastAPI)
```bash
# Using Gunicorn for production
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Or use Docker
docker build -t medical-rag-api .
docker run -p 8000:8000 medical-rag-api
```

### Environment Updates for Production
- Set `DEBUG_MODE=False` in backend `.env`
- Update `VITE_API_BASE_URL` to production backend URL
- Restrict CORS to production frontend domain
- Use environment variables or secrets manager for API keys
- Enable HTTPS/SSL for all communications

## Summary

The frontend and backend are now fully integrated with:

✅ HTTP REST API communication via fetch  
✅ Centralized API client for consistent requests  
✅ Real-time chat history via Firebase Firestore  
✅ CORS configured for frontend-backend communication  
✅ Error handling and user-friendly messages  
✅ Structured response format for UI display  
✅ Support for multiple user modes (patient/doctor)  
✅ Safety validation and content filtering  

For questions or issues, refer to the specific troubleshooting section above.
