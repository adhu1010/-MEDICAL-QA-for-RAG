"""
Test script to verify the safety validation fixes
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models import GeneratedAnswer, UserMode
from backend.safety import get_safety_reflector
from backend.generators import get_answer_generator


def test_safety_validation():
    """Test safety validation with problematic answers"""
    print("Testing safety validation fixes...")
    
    # Get safety reflector
    reflector = get_safety_reflector()
    
    # Test case 1: Answer with messy artifacts (should be fixed)
    answer1 = GeneratedAnswer(
        answer="Common side effects include nausea and diarrhea. <FREETEXT> </ABSTRACT> \n\n⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions.",
        confidence=0.8,
        sources=["MedQuAD"],
        reasoning="Test case"
    )
    
    evidence_texts = ["Metformin can cause nausea and diarrhea as common side effects."]
    
    print("\nTest 1: Answer with messy artifacts")
    print(f"Original answer: {answer1.answer}")
    
    safety_check = reflector.validate(answer1, evidence_texts, is_patient_mode=True)
    print(f"Safety check - Is safe: {safety_check.is_safe}")
    print(f"Issues: {safety_check.issues}")
    
    # Test case 2: Clean answer (should pass)
    answer2 = GeneratedAnswer(
        answer="Common side effects include nausea and diarrhea. \n\n⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions.",
        confidence=0.8,
        sources=["MedQuAD"],
        reasoning="Test case"
    )
    
    print("\nTest 2: Clean answer")
    print(f"Original answer: {answer2.answer}")
    
    safety_check2 = reflector.validate(answer2, evidence_texts, is_patient_mode=True)
    print(f"Safety check - Is safe: {safety_check2.is_safe}")
    print(f"Issues: {safety_check2.issues}")


def test_answer_generation():
    """Test answer generation improvements"""
    print("\n\nTesting answer generation improvements...")
    
    # Get answer generator
    generator = get_answer_generator()
    
    # Test fallback generation
    prompt = "What are the side effects of Metformin?"
    evidence_texts = [
        "Q: What are the side effects of Metformin? A: Common side effects include nausea, vomiting, diarrhea, and stomach upset.",
        "Metformin may cause gastrointestinal disturbances in some patients."
    ]
    
    print(f"Testing fallback generation with prompt: {prompt}")
    fallback_answer = generator._generate_fallback(prompt, evidence_texts)
    print(f"Fallback answer: {fallback_answer}")


if __name__ == "__main__":
    test_safety_validation()
    test_answer_generation()
    print("\n\nTests completed!")