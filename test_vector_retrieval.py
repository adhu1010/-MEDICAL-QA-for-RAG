"""
Test Vector Retrieval Functionality
====================================

This script comprehensively tests the vector retrieval system:
1. Vector store statistics
2. Embedding generation
3. Similarity search
4. Confidence scoring
5. Query expansion
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.retrievers.vector_retriever import VectorRetriever
from backend.models import ProcessedQuery, UserMode
from backend.preprocessing.query_processor import QueryPreprocessor
from loguru import logger
import time

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_vector_store_stats():
    """Test 1: Check vector store statistics"""
    print_section("TEST 1: Vector Store Statistics")
    
    try:
        retriever = VectorRetriever()
        stats = retriever.get_collection_stats()
        
        print(f"✓ Collection Name: {stats.get('collection_name')}")
        print(f"✓ Document Count: {stats.get('document_count'):,}")
        print(f"✓ Embedding Model: {stats.get('embedding_model')}")
        
        if stats.get('document_count', 0) == 0:
            print("\n⚠️  WARNING: Vector store is empty! Run build_vector_store.py first")
            return False
        
        print("\n✓ Vector store is properly initialized")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_embedding_generation():
    """Test 2: Test embedding generation"""
    print_section("TEST 2: Embedding Generation")
    
    try:
        retriever = VectorRetriever()
        
        test_texts = [
            "What causes diabetes?",
            "How to treat hypertension?",
            "Side effects of aspirin"
        ]
        
        print("Testing embedding generation for sample queries:\n")
        
        for text in test_texts:
            start_time = time.time()
            embedding = retriever.embed_text(text)
            elapsed = time.time() - start_time
            
            print(f"  Query: '{text}'")
            print(f"    - Embedding dimension: {len(embedding)}")
            print(f"    - Time: {elapsed:.3f}s")
            print(f"    - First 5 values: {embedding[:5]}")
            print()
            
            if len(embedding) == 0:
                print(f"✗ Failed to generate embedding for: {text}")
                return False
        
        print("✓ All embeddings generated successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_basic_retrieval():
    """Test 3: Basic similarity search"""
    print_section("TEST 3: Basic Similarity Search")
    
    try:
        retriever = VectorRetriever()
        preprocessor = QueryPreprocessor()
        
        test_queries = [
            "What is diabetes?",
            "How does chemotherapy work?",
            "What are the symptoms of COVID-19?",
            "Treatment for heart attack"
        ]
        
        print("Testing retrieval for medical queries:\n")
        
        for query_text in test_queries:
            # Preprocess query
            query = preprocessor.process_query(query_text)
            
            # Retrieve documents
            start_time = time.time()
            results = retriever.retrieve(query, top_k=5)
            elapsed = time.time() - start_time
            
            print(f"Query: '{query_text}'")
            print(f"  - Retrieved {len(results)} documents in {elapsed:.3f}s")
            
            if results:
                print(f"  - Top result confidence: {results[0].confidence:.4f}")
                print(f"  - Top result preview: {results[0].content[:200]}...")
            else:
                print(f"  - ⚠️  No results found above threshold")
            print()
        
        print("✓ Basic retrieval test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_confidence_scoring():
    """Test 4: Confidence score distribution"""
    print_section("TEST 4: Confidence Score Analysis")
    
    try:
        retriever = VectorRetriever()
        preprocessor = QueryPreprocessor()
        
        # Test with different query types
        test_cases = [
            ("What is diabetes mellitus type 2?", "Highly specific medical query"),
            ("Tell me about health", "Vague general query"),
            ("asdfghjkl qwerty", "Random gibberish"),
        ]
        
        print("Analyzing confidence scores for different query types:\n")
        
        for query_text, description in test_cases:
            query = preprocessor.process_query(query_text)
            results = retriever.retrieve(query, top_k=10)
            
            print(f"{description}")
            print(f"  Query: '{query_text}'")
            print(f"  Results: {len(results)}")
            
            if results:
                confidences = [r.confidence for r in results]
                print(f"  Confidence range: {min(confidences):.4f} - {max(confidences):.4f}")
                print(f"  Average confidence: {sum(confidences)/len(confidences):.4f}")
            else:
                print(f"  No results above threshold")
            print()
        
        print("✓ Confidence scoring analysis complete")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_medical_entities():
    """Test 5: Medical entity recognition in retrieval"""
    print_section("TEST 5: Medical Entity Recognition")
    
    try:
        retriever = VectorRetriever()
        preprocessor = QueryPreprocessor()
        
        # Queries with medical entities
        test_queries = [
            "What is metformin used for?",  # Drug
            "Symptoms of pneumonia",  # Disease
            "ACE inhibitors side effects",  # Drug class
            "MRI scan procedure",  # Procedure
        ]
        
        print("Testing retrieval for queries with medical entities:\n")
        
        for query_text in test_queries:
            query = preprocessor.process_query(query_text)
            
            print(f"Query: '{query_text}'")
            print(f"  Detected entities: {query.entities}")
            
            results = retriever.retrieve(query, top_k=3)
            
            if results:
                print(f"  Retrieved {len(results)} relevant documents")
                for i, result in enumerate(results[:2], 1):
                    print(f"    {i}. Confidence: {result.confidence:.4f}")
                    print(f"       Preview: {result.content[:150]}...")
            else:
                print(f"  No results found")
            print()
        
        print("✓ Medical entity recognition test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mode_specific_retrieval():
    """Test 6: Mode-specific retrieval (DOCTOR vs PATIENT)"""
    print_section("TEST 6: Mode-Specific Retrieval")
    
    try:
        retriever = VectorRetriever()
        preprocessor = QueryPreprocessor()
        
        # Same topic, different modes
        test_cases = [
            ("What are the differential diagnoses for chest pain?", UserMode.DOCTOR),
            ("Why does my chest hurt?", UserMode.PATIENT),
        ]
        
        print("Comparing retrieval for DOCTOR vs PATIENT modes:\n")
        
        for query_text, expected_mode in test_cases:
            query = preprocessor.process_query(query_text)
            
            print(f"Query: '{query_text}'")
            print(f"  Expected mode: {expected_mode}")
            print(f"  Detected mode: {query.detected_mode}")
            
            results = retriever.retrieve(query, top_k=3)
            
            if results:
                print(f"  Retrieved {len(results)} documents")
                print(f"  Top confidence: {results[0].confidence:.4f}")
            print()
        
        print("✓ Mode-specific retrieval test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_batch_processing():
    """Test 7: Batch query processing"""
    print_section("TEST 7: Batch Query Processing Performance")
    
    try:
        retriever = VectorRetriever()
        preprocessor = QueryPreprocessor()
        
        # Multiple queries
        queries = [
            "What is hypertension?",
            "Diabetes symptoms",
            "Heart disease prevention",
            "Cancer treatment options",
            "COVID-19 vaccine safety",
        ]
        
        print(f"Processing {len(queries)} queries in batch:\n")
        
        start_time = time.time()
        
        all_results = []
        for query_text in queries:
            query = preprocessor.process_query(query_text)
            results = retriever.retrieve(query, top_k=5)
            all_results.append((query_text, results))
        
        elapsed = time.time() - start_time
        
        print(f"✓ Processed {len(queries)} queries in {elapsed:.2f}s")
        print(f"  Average time per query: {elapsed/len(queries):.3f}s")
        print()
        
        # Show summary
        for query_text, results in all_results:
            print(f"  '{query_text}': {len(results)} results")
        
        print(f"\n✓ Batch processing test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_similarity_threshold():
    """Test 8: Similarity threshold filtering"""
    print_section("TEST 8: Similarity Threshold Testing")
    
    try:
        retriever = VectorRetriever()
        preprocessor = QueryPreprocessor()
        
        query = preprocessor.process_query("What is diabetes?")
        
        # Get raw results from ChromaDB
        query_embedding = retriever.embed_text(query.normalized_question)
        
        raw_results = retriever.collection.query(
            query_embeddings=[query_embedding],
            n_results=20,
            include=["documents", "distances"]
        )
        
        print("Analyzing similarity scores and threshold:\n")
        print(f"Query: '{query.original_question}'")
        print(f"Total raw results: {len(raw_results['documents'][0])}")
        print()
        
        # Show distance distribution
        distances = raw_results['distances'][0]
        similarities = [1.0 - d for d in distances]
        
        print("Distance to Similarity conversion:")
        for i in range(min(10, len(distances))):
            distance = distances[i]
            similarity = similarities[i]
            status = "✓" if similarity >= 0.3 else "✗"
            print(f"  {i+1}. Distance: {distance:.4f} → Similarity: {similarity:.4f} {status}")
        
        print()
        
        # Apply threshold filter
        filtered_results = retriever.retrieve(query, top_k=20)
        print(f"After threshold filtering (≥0.3): {len(filtered_results)} results")
        
        print(f"\n✓ Threshold filtering test complete")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all vector retrieval tests"""
    print("\n" + "█" * 80)
    print("  MEDICAL RAG - VECTOR RETRIEVAL TEST SUITE")
    print("█" * 80)
    
    tests = [
        ("Vector Store Statistics", test_vector_store_stats),
        ("Embedding Generation", test_embedding_generation),
        ("Basic Similarity Search", test_basic_retrieval),
        ("Confidence Score Analysis", test_confidence_scoring),
        ("Medical Entity Recognition", test_medical_entities),
        ("Mode-Specific Retrieval", test_mode_specific_retrieval),
        ("Batch Query Processing", test_batch_processing),
        ("Similarity Threshold Testing", test_similarity_threshold),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Vector retrieval is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
    
    return results


if __name__ == "__main__":
    run_all_tests()
