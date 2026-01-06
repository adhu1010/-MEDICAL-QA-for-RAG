"""
Test script for generating safe answers without citations
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.generators import get_answer_generator
from backend.safety import get_safety_reflector
from backend.models import ProcessedQuery, FusedEvidence, RetrievedEvidence, UserMode

def test_safe_answer_without_citations():
    """Test generating a safe answer without citations"""
    print("=" * 60)
    print("Testing Safe Answer Generation Without Citations")
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
    
    # Get generator and safety reflector
    print("\n2. Loading components...")
    generator = get_answer_generator(model_type="huggingface")
    reflector = get_safety_reflector()
    
    if generator.model:
        print("✓ BioGPT loaded successfully!")
        
        # Generate regular answer
        print("\n3. Generating regular answer with citations...")
        regular_answer = generator.generate(query, evidence, mode=UserMode.PATIENT)
        
        # Generate answer without citations
        print("\n4. Generating safe answer without citations...")
        safe_answer = generator.generate_without_citations(query, evidence, mode=UserMode.PATIENT)
        
        # Display results
        print("\n" + "=" * 60)
        print("REGULAR ANSWER (with citations):")
        print("=" * 60)
        print(f"\nAnswer:\n{regular_answer.answer}")
        print(f"\nConfidence: {regular_answer.confidence * 100:.1f}%")
        print(f"Sources: {len(regular_answer.sources)}")
        print(f"Reasoning: {regular_answer.reasoning}")
        
        print("\n" + "=" * 60)
        print("SAFE ANSWER (without citations):")
        print("=" * 60)
        print(f"\nAnswer:\n{safe_answer.answer}")
        print(f"\nConfidence: {safe_answer.confidence * 100:.1f}%")
        print(f"Sources: {len(safe_answer.sources)}")
        print(f"Reasoning: {safe_answer.reasoning}")
        
        print("\n" + "=" * 60)
        print("COMPARISON:")
        print("=" * 60)
        print(f"Regular answer has citations: {len(regular_answer.sources) > 0}")
        print(f"Safe answer has citations: {len(safe_answer.sources) > 0}")
        print(f"Confidence difference: {abs(regular_answer.confidence - safe_answer.confidence):.2f}")
        
        print("\n✓ Test completed successfully!")
        
    else:
        print("\n✗ BioGPT failed to load")
        print("Will use evidence-based fallback instead")

if __name__ == "__main__":
    test_safe_answer_without_citations()