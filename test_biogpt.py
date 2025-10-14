"""
Download and test BioGPT-Large
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.generators import get_answer_generator
from backend.models import ProcessedQuery, FusedEvidence, RetrievedEvidence, UserMode

print("=" * 60)
print("Downloading and Testing BioGPT-Large")
print("=" * 60)
print("\nThis will download ~6.3 GB. Please wait...")
print("Progress will be shown below:\n")

# Get generator (will download BioGPT)
print("1. Loading BioGPT-Large (this may take 5-10 minutes)...")
generator = get_answer_generator(model_type="huggingface")

if generator.model:
    print("\n✓ BioGPT loaded successfully!")
    print(f"  Model: {generator.model.__class__.__name__}")
    print(f"  Parameters: ~1.5 billion")
    
    # Create test query and evidence
    print("\n2. Creating test medical query...")
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
    
    # Generate answer
    print("\n3. Generating medical answer with BioGPT...")
    result = generator.generate(query, evidence, mode=UserMode.PATIENT)
    
    print("\n" + "=" * 60)
    print("BIOGPT RESULT:")
    print("=" * 60)
    print(f"\nAnswer:\n{result.answer}")
    print(f"\nConfidence: {result.confidence * 100:.1f}%")
    print(f"Sources: {len(result.sources)}")
    print("=" * 60)
    
else:
    print("\n✗ BioGPT failed to load")
    print("Will use evidence-based fallback instead")
