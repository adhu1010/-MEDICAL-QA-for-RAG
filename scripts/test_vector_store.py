"""
Quick test to verify vector store has documents
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retrievers import get_vector_retriever
from backend.models import MedicalQuery, UserMode

def main():
    print("Testing vector store...")
    
    # Get retriever
    retriever = get_vector_retriever()
    
    # Get stats
    stats = retriever.get_collection_stats()
    print(f"\nVector Store Stats:")
    print(f"  Collection: {stats.get('collection_name')}")
    print(f"  Document Count: {stats.get('document_count')}")
    print(f"  Embedding Model: {stats.get('embedding_model')}")
    
    # Test query
    from backend.preprocessing import get_query_preprocessor
    preprocessor = get_query_preprocessor()
    
    test_questions = [
        "What are the side effects of Metformin?",
        "How does Metformin work?",
        "What is the best antibiotic for sinus infection?"
    ]
    
    print("\n" + "="*60)
    print("Testing retrieval:")
    print("="*60)
    
    for question in test_questions:
        print(f"\nQ: {question}")
        
        # Process query
        query = MedicalQuery(question=question, mode=UserMode.PATIENT)
        processed = preprocessor.process_query(query)
        
        # Retrieve
        evidences = retriever.retrieve(processed, top_k=3)
        
        print(f"  Found {len(evidences)} evidences")
        for i, ev in enumerate(evidences, 1):
            print(f"  [{i}] Confidence: {ev.confidence:.2f}")
            print(f"      Content: {ev.content[:100]}...")
            print(f"      Source: {ev.metadata.get('source', 'unknown')}")

if __name__ == "__main__":
    main()
