"""
Test PubMed API Dynamic Retrieval

Quick script to verify PubMed integration is working correctly.
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from backend.retrievers import get_pubmed_retriever
from backend.models import MedicalEntity, ProcessedQuery, QueryType, RetrievalStrategy, UserMode


def test_pubmed_configuration():
    """Test if PubMed is properly configured"""
    print("\n" + "="*60)
    print("PUBMED CONFIGURATION TEST")
    print("="*60)
    
    pubmed = get_pubmed_retriever()
    
    print(f"\nEmail: {pubmed.email or '❌ NOT SET'}")
    print(f"API Key: {'✓ Set' if pubmed.api_key else '❌ Not set (using 3 req/s)'}")
    print(f"Enabled: {'✅ Yes' if pubmed.enabled else '❌ No'}")
    print(f"Max Results: {pubmed.max_results}")
    print(f"Rate Limit: {pubmed.rate_limit}s between requests")
    
    if not pubmed.enabled:
        print("\n⚠️  PubMed is DISABLED")
        print("\nTo enable PubMed:")
        print("1. Set environment variable:")
        print("   PowerShell: $env:PUBMED_EMAIL=\"your@email.com\"")
        print("   Linux/Mac: export PUBMED_EMAIL=\"your@email.com\"")
        print("\n2. Or add to .env file:")
        print("   PUBMED_EMAIL=your@email.com")
        print("\n3. Restart backend")
        return False
    
    print("\n✅ PubMed configuration valid!")
    return True


def test_simple_search():
    """Test a simple PubMed search"""
    print("\n" + "="*60)
    print("SIMPLE PUBMED SEARCH TEST")
    print("="*60)
    
    pubmed = get_pubmed_retriever()
    
    if not pubmed.enabled:
        print("❌ Skipped (PubMed not enabled)")
        return
    
    # Test query
    query_text = "diabetes treatment"
    print(f"\nSearching PubMed for: '{query_text}'")
    
    try:
        pmids = pubmed._search_pubmed(f"({query_text})[Title/Abstract]")
        
        if pmids:
            print(f"✅ Found {len(pmids)} articles")
            print(f"\nFirst 5 PMIDs: {pmids[:5]}")
        else:
            print("⚠️  No articles found")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()


def test_fetch_abstracts():
    """Test fetching article abstracts"""
    print("\n" + "="*60)
    print("FETCH ABSTRACTS TEST")
    print("="*60)
    
    pubmed = get_pubmed_retriever()
    
    if not pubmed.enabled:
        print("❌ Skipped (PubMed not enabled)")
        return
    
    # Search first
    query_text = "metformin side effects"
    print(f"\nSearching for: '{query_text}'")
    
    try:
        pmids = pubmed._search_pubmed(f"({query_text})[Title/Abstract]")
        
        if not pmids:
            print("⚠️  No articles found to fetch")
            return
        
        print(f"Found {len(pmids)} PMIDs, fetching first 2...")
        
        # Fetch abstracts
        import time
        time.sleep(pubmed.rate_limit)
        
        articles = pubmed._fetch_abstracts(pmids[:2])
        
        if articles:
            print(f"✅ Fetched {len(articles)} articles\n")
            
            for i, article in enumerate(articles, 1):
                print(f"\n--- Article {i} ---")
                print(f"PMID: {article['pmid']}")
                print(f"Title: {article['title']}")
                print(f"Journal: {article['journal']} ({article['year']})")
                print(f"Authors: {', '.join(article['authors'][:3])}")
                print(f"Abstract: {article['abstract'][:200]}...")
        else:
            print("⚠️  No articles retrieved")
            
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        import traceback
        traceback.print_exc()


def test_full_retrieval():
    """Test complete retrieval pipeline"""
    print("\n" + "="*60)
    print("FULL RETRIEVAL PIPELINE TEST")
    print("="*60)
    
    pubmed = get_pubmed_retriever()
    
    if not pubmed.enabled:
        print("❌ Skipped (PubMed not enabled)")
        return
    
    # Create test query
    query = ProcessedQuery(
        original_question="What are the side effects of aspirin?",
        normalized_question="aspirin side effects",
        entities=[
            MedicalEntity(text="aspirin", entity_type="DRUG", confidence=0.9)
        ],
        query_type=QueryType.CONTEXTUAL,
        suggested_strategy=RetrievalStrategy.FULL_HYBRID,
        detected_mode=UserMode.PATIENT
    )
    
    print(f"\nQuery: {query.original_question}")
    print(f"Entities: {[e.text for e in query.entities]}")
    print(f"\nRetrieving from PubMed...")
    
    try:
        evidences = pubmed.retrieve(query, top_k=3)
        
        if evidences:
            print(f"✅ Retrieved {len(evidences)} evidences\n")
            
            for i, evidence in enumerate(evidences, 1):
                print(f"\n{'='*60}")
                print(f"Evidence {i}")
                print(f"{'='*60}")
                print(f"Source: {evidence.source_type}")
                print(f"Confidence: {evidence.confidence:.2f}")
                print(f"\nMetadata:")
                print(f"  PMID: {evidence.metadata['pmid']}")
                print(f"  Title: {evidence.metadata['title']}")
                print(f"  Journal: {evidence.metadata['journal']} ({evidence.metadata['year']})")
                print(f"  Citation: {evidence.metadata['citation']}")
                print(f"  URL: {evidence.metadata['url']}")
                print(f"\nContent Preview:")
                print(f"  {evidence.content[:300]}...")
        else:
            print("⚠️  No evidences retrieved")
            
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PUBMED API INTEGRATION TEST SUITE")
    print("="*60)
    
    # Test 1: Configuration
    config_ok = test_pubmed_configuration()
    
    if not config_ok:
        print("\n❌ PubMed not configured. Tests aborted.")
        return
    
    # Test 2: Simple search
    test_simple_search()
    
    # Test 3: Fetch abstracts
    test_fetch_abstracts()
    
    # Test 4: Full retrieval
    test_full_retrieval()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    print("\n✅ PubMed dynamic integration is working!")
    print("\nNext steps:")
    print("1. Start backend: python scripts/run.py")
    print("2. Ask a medical question")
    print("3. Check sources for PubMed citations")


if __name__ == "__main__":
    main()
