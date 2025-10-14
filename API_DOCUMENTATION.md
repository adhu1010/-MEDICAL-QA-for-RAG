# 📘 API Documentation - Medical RAG QA System

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. For production, implement JWT or API key authentication.

---

## Endpoints

### 1. Health Check

Check system health and component status.

**Endpoint:** `GET /api/health`

**Response:**
```json
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

**Status Codes:**
- `200` - System healthy
- `500` - System unhealthy

---

### 2. Ask Medical Question (Main Endpoint)

Submit a medical question and receive an AI-generated answer with evidence.

**Endpoint:** `POST /api/ask`

**Request Body:**
```json
{
  "question": "What are the side effects of Metformin?",
  "mode": "patient"  // or "doctor"
}
```

**Parameters:**
- `question` (string, required): The medical question to answer
- `mode` (string, optional): User mode - "patient" or "doctor". Default: "patient"

**Response:**
```json
{
  "question": "What are the side effects of Metformin?",
  "answer": "Common side effects of Metformin include nausea, stomach upset, and diarrhea. Rarely, it may cause lactic acidosis...",
  "mode": "patient",
  "sources": [
    "vector: Metformin",
    "kg: Metformin",
    "vector: Type2Diabetes"
  ],
  "confidence": 0.85,
  "safety_validated": true,
  "metadata": {
    "retrieval_strategy": "hybrid",
    "entities_found": 2,
    "evidence_count": 5,
    "query_type": "contextual",
    "safety_issues": []
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request
- `500` - Server error

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the side effects of Metformin?",
    "mode": "patient"
  }'
```

**Example (Python):**
```python
import requests

response = requests.post("http://localhost:8000/api/ask", json={
    "question": "What are the side effects of Metformin?",
    "mode": "patient"
})

data = response.json()
print(data["answer"])
```

---

### 3. Preprocess Query

Analyze a query to extract entities and determine query type (for debugging/analysis).

**Endpoint:** `POST /api/preprocess`

**Request Body:**
```json
{
  "question": "What are the side effects of Metformin?",
  "mode": "patient"
}
```

**Response:**
```json
{
  "original_question": "What are the side effects of Metformin?",
  "normalized_question": "What are the side effects of Metformin",
  "entities": [
    {
      "text": "Metformin",
      "entity_type": "CHEMICAL",
      "umls_concept": "C0025598",
      "confidence": 0.8
    }
  ],
  "query_type": "contextual",
  "suggested_strategy": "hybrid"
}
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

### 4. System Statistics

Get statistics about the vector store and knowledge graph.

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "vector_store": {
    "collection_name": "medical_documents",
    "document_count": 8,
    "embedding_model": "dmis-lab/biobert-base-cased-v1.2"
  },
  "knowledge_graph": {
    "nodes": 45,
    "edges": 67
  }
}
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

## Data Models

### MedicalQuery

```json
{
  "question": "string (required)",
  "mode": "patient | doctor (optional, default: patient)"
}
```

### MedicalAnswer

```json
{
  "question": "string",
  "answer": "string",
  "mode": "patient | doctor",
  "sources": ["array of strings"],
  "confidence": "float (0-1)",
  "safety_validated": "boolean",
  "metadata": {
    "retrieval_strategy": "kg_only | vector_only | hybrid",
    "entities_found": "integer",
    "evidence_count": "integer",
    "query_type": "definition | contextual | complex",
    "safety_issues": ["array of strings"]
  }
}
```

### ProcessedQuery

```json
{
  "original_question": "string",
  "normalized_question": "string",
  "entities": [
    {
      "text": "string",
      "entity_type": "string",
      "umls_concept": "string (optional)",
      "confidence": "float"
    }
  ],
  "query_type": "definition | contextual | complex",
  "suggested_strategy": "kg_only | vector_only | hybrid"
}
```

---

## User Modes

### Patient Mode
- **Purpose:** General public, patients seeking medical information
- **Output:** Simplified language, easy to understand
- **Safety:** Includes mandatory disclaimers to consult healthcare professionals
- **Example:** "Metformin may cause stomach upset. Always talk to your doctor."

### Doctor Mode
- **Purpose:** Healthcare professionals, medical students
- **Output:** Technical terminology, detailed explanations
- **Citations:** Includes source citations from medical literature
- **Example:** "Metformin (C0025598) exhibits gastrointestinal adverse effects in 20-30% of patients [PMID: 12345]."

---

## Retrieval Strategies

The system automatically chooses the best retrieval strategy based on query analysis:

### 1. KG Only
- **When:** Definition queries, simple fact lookups
- **Example:** "What is Type 2 Diabetes?"
- **Uses:** Knowledge graph relationships only

### 2. Vector Only
- **When:** Contextual queries without clear entities
- **Example:** "How to manage diabetes?"
- **Uses:** Semantic search in document embeddings

### 3. Hybrid (Default)
- **When:** Complex queries, queries with multiple entities
- **Example:** "What are the side effects of Metformin?"
- **Uses:** Both knowledge graph AND vector search, then fuses results

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Common Errors

**400 Bad Request:**
- Missing required fields
- Invalid mode value

**500 Internal Server Error:**
- Model loading failure
- Database connection issues
- Processing errors

---

## Rate Limiting

Currently no rate limiting. For production:
- Implement rate limiting per IP/user
- Suggested: 100 requests per hour for public API
- Suggested: 1000 requests per hour for authenticated users

---

## Interactive Documentation

Visit these URLs when the server is running:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide:
- Interactive API testing
- Request/response examples
- Schema documentation
- Try-it-out functionality

---

## WebSocket Support (Future)

Future versions may include WebSocket support for:
- Real-time streaming answers
- Progress updates during retrieval
- Multi-turn conversations

---

## Sample Requests

### 1. Simple Patient Question

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is diabetes?",
    "mode": "patient"
  }'
```

### 2. Medical Professional Query

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the mechanism of action of Metformin in Type 2 Diabetes",
    "mode": "doctor"
  }'
```

### 3. Treatment Question

```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the best antibiotic for sinus infection?",
    "mode": "patient"
  }'
```

### 4. Preprocessing Only

```bash
curl -X POST "http://localhost:8000/api/preprocess" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the side effects of Metformin?"
  }'
```

---

## Best Practices

### For Developers

1. **Always validate safety_validated flag** in responses
2. **Check confidence scores** - values below 0.5 may be unreliable
3. **Display sources** to users for transparency
4. **Handle errors gracefully** with user-friendly messages
5. **Cache responses** for identical queries to reduce load

### For Users

1. **Patient mode** is safer for general public
2. **Always consult professionals** - this is educational only
3. **Check sources** to verify information credibility
4. **Report issues** if answers seem incorrect

---

## Versioning

Current version: **1.0.0**

API versioning will be added in future releases:
- `/api/v1/ask` - Version 1
- `/api/v2/ask` - Version 2 (when available)

---

## Security Considerations

⚠️ **Important for Production:**

1. Add authentication (JWT tokens)
2. Implement rate limiting
3. Sanitize all inputs
4. Use HTTPS only
5. Add CORS restrictions
6. Implement request validation
7. Add audit logging
8. Encrypt sensitive data

---

## Support

For API issues:
- Check server logs: `logs/app.log`
- Review this documentation
- Test with `/api/health` endpoint
- Use interactive docs at `/docs`
