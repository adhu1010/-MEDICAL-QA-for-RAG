"""
Unit tests for data models
"""
import pytest
from backend.models import MedicalQuery, MedicalAnswer, HealthResponse, ProcessedQuery, UserMode


def test_medical_query_model():
    """Test MedicalQuery model creation and validation"""
    query = MedicalQuery(
        question="What is diabetes?",
        mode=UserMode.PATIENT
    )

    assert query.question == "What is diabetes?"
    assert query.mode == UserMode.PATIENT


def test_medical_answer_model():
    """Test MedicalAnswer model creation and validation"""
    answer = MedicalAnswer(
        question="What is diabetes?",
        answer="Diabetes is a chronic condition...",
        mode=UserMode.PATIENT,
        confidence=0.85,
        safety_validated=True
    )

    assert answer.question == "What is diabetes?"
    assert "chronic condition" in answer.answer
    assert answer.confidence == 0.85
    assert answer.safety_validated is True


def test_health_response_model():
    """Test HealthResponse model creation and validation"""
    response = HealthResponse(
        status="healthy",
        version="1.0.0",
        components={"preprocessor": "ready"}
    )

    assert response.status == "healthy"
    assert response.version == "1.0.0"
    assert response.components["preprocessor"] == "ready"


def test_processed_query_model():
    """Test ProcessedQuery model creation and validation"""
    processed = ProcessedQuery(
        original_question="What is diabetes?",
        entities=["diabetes"],
        detected_mode=UserMode.PATIENT,
        suggested_strategy="vector",
        query_type="definitional"
    )

    assert processed.original_question == "What is diabetes?"
    assert "diabetes" in processed.entities
    assert processed.detected_mode == UserMode.PATIENT
