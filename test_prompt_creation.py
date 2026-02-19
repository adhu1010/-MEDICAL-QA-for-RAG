"""
Test script for prompt creation without citations
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.generators.answer_generator import AnswerGenerator
from backend.models import ProcessedQuery, FusedEvidence, RetrievedEvidence, UserMode

def test_prompt_creation():
    """Test creating prompts without citations"""
    print("=" * 60)
    print("Testing Prompt Creation Without Citations")
    print("=" * 60)
    
    # Create test query and evidence
    print("\n1. Creating test medical query...")
    query = ProcessedQuery(
        original_question="What are the side effects of Metformin?",
        normalized_question="side effects metformin",
        entities=[],
        query_type="contextual",
        suggested_strategy="vector_only"
    )
    
    evidence = FusedEvidence(
        evidences=[
            RetrievedEvidence(
                source_type="vector",
                content="Common side effects of Metformin include nausea, vomiting, stomach upset, diarrhea, weakness, and a metallic taste in the mouth. Rarely, it may cause lactic acidosis, a serious condition.",
                confidence=0.9,
                metadata={"source": "medquad", "category": "Diabetes"}
            ),
            RetrievedEvidence(
                source_type="vector",
                content="Metformin is the first-line medication for type 2 diabetes. This meta-analysis of 100 studies shows that metformin effectively reduces HbA1c levels by 1-2% and has cardiovascular benefits. Common side effects include gastrointestinal disturbances in 20-30% of patients.",
                confidence=0.88,
                metadata={"source": "pubmed", "pmid": "12345678"}
            )
        ],
        combined_confidence=0.89,
        fusion_method="vector_only"
    )
    
    # Create answer generator (without loading model)
    print("\n2. Creating answer generator...")
    generator = AnswerGenerator(model_type="huggingface")
    
    # Test prompt creation with citations
    print("\n3. Creating prompt WITH citations...")
    prompt_with_citations = generator._create_prompt(query, evidence, UserMode.PATIENT)
    
    # Test prompt creation without citations
    print("\n4. Creating prompt WITHOUT citations...")
    prompt_without_citations = generator._create_prompt_without_citations(query, evidence, UserMode.PATIENT)
    
    # Display results
    print("\n" + "=" * 60)
    print("PROMPT WITH CITATIONS:")
    print("=" * 60)
    print(prompt_with_citations)
    
    print("\n" + "=" * 60)
    print("PROMPT WITHOUT CITATIONS:")
    print("=" * 60)
    print(prompt_without_citations)
    
    # Check differences
    print("\n" + "=" * 60)
    print("DIFFERENCES:")
    print("=" * 60)
    if "citation" in prompt_with_citations.lower() or "cite" in prompt_with_citations.lower():
        print("✓ Regular prompt includes citation requirements")
    else:
        print("⚠ Regular prompt may not explicitly require citations")
        
    if "citation" not in prompt_without_citations.lower() and "cite" not in prompt_without_citations.lower():
        print("✓ Safe prompt does not require citations")
    else:
        print("⚠ Safe prompt may still include citation requirements")
    
    print("\n✓ Test completed successfully!")

if __name__ == "__main__":
    test_prompt_creation()