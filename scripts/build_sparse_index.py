"""
Build BM25 sparse retrieval index
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retrievers.sparse_retriever import get_sparse_retriever
from backend.config import settings
from loguru import logger
import json

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add(settings.log_file, rotation="500 MB", level="DEBUG")


def load_medquad_documents():
    """Load MedQuAD documents from processed JSON"""
    medquad_file = settings.data_dir / "medquad_processed.json"
    
    if not medquad_file.exists():
        logger.error(f"MedQuAD processed file not found: {medquad_file}")
        logger.info("Run 'python scripts/process_medquad.py' first")
        return [], []
    
    logger.info(f"Loading MedQuAD dataset from {medquad_file}")
    
    with open(medquad_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    metadatas = []
    
    for item in data:
        # Combine question and answer for indexing
        doc_text = f"Question: {item['question']}\nAnswer: {item['answer']}"
        documents.append(doc_text)
        
        metadata = {
            'source': 'MedQuAD',
            'category': item.get('category', 'Unknown'),
            'focus': item.get('focus', 'General'),
            'question': item['question']
        }
        metadatas.append(metadata)
    
    logger.info(f"Loaded {len(documents)} MedQuAD documents")
    return documents, metadatas


def load_pubmed_documents():
    """Load sample PubMed documents"""
    # Sample PubMed abstracts for testing
    # In production, this would load from actual PubMed data
    documents = [
        "Metformin is a biguanide antihyperglycemic agent used for treating non-insulin-dependent diabetes mellitus (NIDDM). "
        "It improves glycemic control by decreasing hepatic glucose production, decreasing glucose absorption and increasing insulin-mediated glucose uptake.",
        
        "Hypertension is a common condition in which the long-term force of the blood against artery walls is high enough to cause health problems. "
        "Treatment typically includes lifestyle changes and medications such as ACE inhibitors, ARBs, calcium channel blockers, and diuretics.",
        
        "Type 2 diabetes is characterized by insulin resistance and relative insulin deficiency. "
        "First-line treatment includes metformin, along with lifestyle modifications including diet and exercise."
    ]
    
    metadatas = [
        {'source': 'PubMed', 'pmid': 'SAMPLE001', 'title': 'Metformin Overview'},
        {'source': 'PubMed', 'pmid': 'SAMPLE002', 'title': 'Hypertension Treatment'},
        {'source': 'PubMed', 'pmid': 'SAMPLE003', 'title': 'Type 2 Diabetes Management'}
    ]
    
    logger.info(f"Loaded {len(documents)} PubMed documents")
    return documents, metadatas


def build_sparse_index():
    """Build the BM25 sparse index"""
    logger.info("Building BM25 sparse index")
    
    # Get retriever
    retriever = get_sparse_retriever()
    
    # Load documents
    medquad_docs, medquad_meta = load_medquad_documents()
    pubmed_docs, pubmed_meta = load_pubmed_documents()
    
    # Combine all documents
    all_documents = medquad_docs + pubmed_docs
    all_metadatas = medquad_meta + pubmed_meta
    
    # Generate IDs
    ids = [f"doc_{i}" for i in range(len(all_documents))]
    
    if not all_documents:
        logger.error("No documents to add to BM25 index!")
        return False
    
    # Build index
    logger.info(f"Building BM25 index for {len(all_documents)} documents")
    success = retriever.build_index(
        documents=all_documents,
        metadatas=all_metadatas,
        ids=ids
    )
    
    if success:
        logger.info("✓ BM25 sparse index built successfully")
        
        # Show stats
        stats = retriever.get_stats()
        logger.info(f"Stats: {stats}")
    else:
        logger.error("✗ Failed to build BM25 index")
    
    return success


def main():
    """Main function"""
    logger.info("Starting BM25 sparse index build process")
    
    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    
    # Build sparse index
    success = build_sparse_index()
    
    if success:
        logger.info("\n✓ BM25 sparse index build complete!")
        logger.info(f"Location: {settings.data_dir / 'bm25_index.pkl'}")
        logger.info("\nYou can now use sparse retrieval in your queries!")
    else:
        logger.error("\n✗ BM25 index build failed")
        logger.info("Make sure to run 'python scripts/process_medquad.py' first")


if __name__ == "__main__":
    main()
