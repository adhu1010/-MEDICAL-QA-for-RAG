"""
Test script to verify BioBERT model loads correctly in offline mode
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_biobert_loading():
    """Test that BioBERT model loads from local directory"""
    print("🔍 Testing BioBERT model loading...")
    
    # Set offline mode
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    
    try:
        from sentence_transformers import SentenceTransformer
        from backend.config import settings
        
        print(f"📁 Model path from config: {settings.embedding_model}")
        
        # Check if model directory exists
        model_path = Path(settings.embedding_model)
        if not model_path.exists():
            print(f"❌ Model directory not found: {model_path}")
            print("   Please ensure BioBERT model is downloaded to this location")
            return False
            
        print(f"✅ Model directory exists: {model_path}")
        
        # List files in model directory
        print("📄 Files in model directory:")
        for file in model_path.iterdir():
            print(f"   - {file.name}")
        
        # Try to load the model
        print("🔄 Loading BioBERT model...")
        model = SentenceTransformer(str(model_path))
        print("✅ BioBERT model loaded successfully!")
        
        # Test embedding generation
        print("📝 Testing embedding generation...")
        test_sentences = [
            "What are the side effects of Metformin?",
            "Diabetes treatment options",
            "Common symptoms of hypertension"
        ]
        
        embeddings = model.encode(test_sentences)
        print(f"✅ Generated embeddings with shape: {embeddings.shape}")
        
        # Test similarity
        print("🔍 Testing similarity calculation...")
        similarities = model.similarity(embeddings[0], embeddings[1:])
        print(f"✅ Similarity scores: {similarities.flatten()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading BioBERT model: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_retriever():
    """Test that vector retriever can initialize with local BioBERT"""
    print("\n🔍 Testing Vector Retriever initialization...")
    
    try:
        from backend.retrievers.vector_retriever import VectorRetriever
        
        print("🔄 Initializing VectorRetriever...")
        retriever = VectorRetriever()
        print("✅ VectorRetriever initialized successfully!")
        
        # Test embedding method
        test_text = "Test medical question about diabetes treatment"
        embedding = retriever.embed_text(test_text)
        print(f"✅ Generated embedding with shape: {len(embedding)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing VectorRetriever: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BIOBERT OFFLINE LOADING TEST")
    print("=" * 60)
    
    success1 = test_biobert_loading()
    success2 = test_vector_retriever()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ BioBERT model is ready for offline use")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Please check the error messages above")
    print("=" * 60)