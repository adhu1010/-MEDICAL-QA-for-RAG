"""
Test LLM loading and generation
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.generators import get_answer_generator
from backend.models import ProcessedQuery, FusedEvidence, RetrievedEvidence, UserMode

print("=" * 60)
print("Testing FLAN-T5-small LLM")
print("=" * 60)

# Get generator (will load FLAN-T5)
print("\n1. Loading answer generator...")
generator = get_answer_generator(model_type="huggingface")

if generator.model:
    print("✓ LLM loaded successfully!")
    print(f"  Model: {generator.model.__class__.__name__}")
else:
    print("✗ LLM failed to load, using fallback")

# Create test query and evidence
print("\n2. Creating test query and evidence...")
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
            content="Common side effects of Metformin include nausea, vomiting, stomach upset, diarrhea, and weakness.",
            confidence=0.9,
            metadata={"source": "medquad"}
        )
    ],
    combined_confidence=0.9,
    fusion_method="vector_only"
)

# Generate answer
print("\n3. Generating answer...")
result = generator.generate(query, evidence, mode=UserMode.PATIENT)

print("\n" + "=" * 60)
print("RESULT:")
print("=" * 60)
print(f"Answer: {result.answer}")
print(f"\nConfidence: {result.confidence * 100:.1f}%")
print(f"Sources: {result.sources}")
print("=" * 60)
