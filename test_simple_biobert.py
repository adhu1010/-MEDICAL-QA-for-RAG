"""
Simple test to verify BioBERT model works with vector retriever
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_simple_embedding():
    """Test simple embedding generation"""
    print("🔍 Testing simple BioBERT embedding...")
    
    # Set offline mode
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    
    try:
        from backend.retrievers.vector_retriever import VectorRetriever
        
        # Initialize retriever
        print("🔄 Initializing VectorRetriever...")
        retriever = VectorRetriever()
        print("✅ VectorRetriever initialized!")
        
        # Test embedding
        test_text = "What are the side effects of Metformin?"
        print(f"📝 Testing with text: {test_text}")
        
        embedding = retriever.embed_text(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
        # Test with a list of texts
        test_texts = [
            "Diabetes treatment options",
            "Common symptoms of hypertension",
            "Aspirin side effects"
        ]
        
        print("📝 Testing with multiple texts...")
        embeddings = [retriever.embed_text(text) for text in test_texts]
        print(f"✅ Generated {len(embeddings)} embeddings with {len(embeddings[0])} dimensions each")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SIMPLE BIOBERT TEST")
    print("=" * 50)
    
    success = test_simple_embedding()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED!")
        print("✅ BioBERT model works with vector retriever")
    else:
        print("❌ TEST FAILED")
    print("=" * 50)