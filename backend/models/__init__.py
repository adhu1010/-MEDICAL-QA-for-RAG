"""
Pydantic models for API requests and responses
"""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class UserMode(str, Enum):
    """User interaction modes"""
    DOCTOR = "doctor"
    PATIENT = "patient"


class QueryType(str, Enum):
    """Types of medical queries"""
    DEFINITION = "definition"
    CONTEXTUAL = "contextual"
    COMPLEX = "complex"


class RetrievalStrategy(str, Enum):
    """Retrieval strategies"""
    KG_ONLY = "kg_only"
    VECTOR_ONLY = "vector_only"
    SPARSE_ONLY = "sparse_only"
    DENSE_SPARSE = "dense_sparse"  # Dense (vector) + Sparse (BM25)
    HYBRID = "hybrid"  # KG + Vector (legacy)
    FULL_HYBRID = "full_hybrid"  # KG + Dense + Sparse


class MedicalQuery(BaseModel):
    """User's medical question"""
    question: str = Field(..., description="The medical question to answer")
    mode: UserMode = Field(UserMode.PATIENT, description="User mode (doctor/patient)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the side effects of Metformin?",
                "mode": "patient"
            }
        }


class MedicalEntity(BaseModel):
    """Extracted medical entity"""
    text: str
    entity_type: str
    umls_concept: Optional[str] = None
    confidence: float


class ProcessedQuery(BaseModel):
    """Query after preprocessing and NER"""
    original_question: str
    normalized_question: str
    entities: List[MedicalEntity]
    query_type: QueryType
    suggested_strategy: RetrievalStrategy
    detected_mode: UserMode = Field(UserMode.PATIENT, description="Auto-detected user mode")


class RetrievedEvidence(BaseModel):
    """Evidence retrieved from vector, sparse, or KG"""
    source_type: str  # "vector" (dense), "sparse" (BM25), or "kg"
    content: str
    confidence: float
    metadata: Dict[str, Any] = {}


class FusedEvidence(BaseModel):
    """Combined evidence from multiple sources"""
    evidences: List[RetrievedEvidence]
    combined_confidence: float
    fusion_method: str
    metadata: Dict[str, Any] = {}  # Metadata about fusion process (e.g., fallback info)


class GeneratedAnswer(BaseModel):
    """LLM-generated answer"""
    answer: str
    confidence: float
    sources: List[str]
    reasoning: Optional[str] = None


class SafetyCheck(BaseModel):
    """Safety validation result"""
    is_safe: bool
    issues: List[str] = []
    suggestions: List[str] = []


class MedicalAnswer(BaseModel):
    """Final answer returned to user"""
    question: str
    answer: str
    mode: UserMode
    sources: List[str]
    confidence: float
    safety_validated: bool
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the side effects of Metformin?",
                "answer": "Common side effects of Metformin include nausea, stomach upset, and diarrhea...",
                "mode": "patient",
                "sources": ["PubMed: PMID12345", "MedQuAD: Diabetes"],
                "confidence": 0.92,
                "safety_validated": True,
                "metadata": {
                    "retrieval_strategy": "hybrid",
                    "entities_found": 2
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: Dict[str, str]
