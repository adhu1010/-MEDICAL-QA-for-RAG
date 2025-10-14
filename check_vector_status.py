"""
Quick Vector Store Status Checker
==================================

This script checks the current status of the vector store without waiting for the build to complete.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.retrievers.vector_retriever import VectorRetriever
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")


def check_vector_store_status():
    """Check current vector store status"""
    
    print("\n" + "=" * 80)
    print("  VECTOR STORE STATUS CHECK")
    print("=" * 80 + "\n")
    
    try:
        retriever = VectorRetriever()
        stats = retriever.get_collection_stats()
        
        doc_count = stats.get('document_count', 0)
        collection_name = stats.get('collection_name', 'unknown')
        model_name = stats.get('embedding_model', 'unknown')
        
        print(f"Collection: {collection_name}")
        print(f"Embedding Model: {model_name}")
        print(f"\nCurrent Document Count: {doc_count:,}")
        
        # Calculate progress
        total_expected = 16410
        if doc_count > 0:
            progress = (doc_count / total_expected) * 100
            print(f"Progress: {progress:.1f}% ({doc_count:,} / {total_expected:,})")
            
            # Estimate which batch
            batch_num = (doc_count // 5000) + 1
            docs_in_batch = doc_count % 5000 if doc_count % 5000 > 0 else 5000
            print(f"Current Batch: {batch_num} ({docs_in_batch:,} documents processed)")
        else:
            print("Progress: 0% (Build not started or failed)")
        
        print()
        
        # Status message
        if doc_count == 0:
            print("⚠️  Vector store is empty")
            print("   → Run: python scripts/build_vector_store.py")
        elif doc_count < total_expected:
            print("🔄 Vector store build in progress...")
            print(f"   → {total_expected - doc_count:,} documents remaining")
            print("   → Check back in a few minutes")
        else:
            print("✅ Vector store build complete!")
            print("   → Ready to test with: python test_vector_retrieval.py")
        
        print()
        
        return doc_count
        
    except Exception as e:
        print(f"❌ Error checking vector store: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    check_vector_store_status()
