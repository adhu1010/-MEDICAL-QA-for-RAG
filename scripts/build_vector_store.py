"""
Build vector store from medical documents
"""
import json
from pathlib import Path
import sys

try:
    from loguru import logger
except ImportError:
    class SimpleLogger:
        def info(self, msg): print(msg)
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    logger = SimpleLogger()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retrievers import get_vector_retriever
from backend.config import settings


def load_medquad_documents():
    """Load MedQuAD QA pairs from processed JSON"""
    # First try to load the full processed dataset
    processed_file = Path("../data/medquad_processed.json")
    
    if processed_file.exists():
        logger.info(f"Loading full MedQuAD dataset from {processed_file}")
        with open(processed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        metadatas = []
        
        for item in data:
            # Combine question and answer as document
            doc_text = f"Q: {item['question']}\nA: {item['answer']}"
            documents.append(doc_text)
            
            metadatas.append({
                "source": "medquad",
                "category": item.get("category", "Unknown"),
                "focus": item.get("focus", "")
            })
        
        logger.info(f"Loaded {len(documents)} MedQuAD documents from full dataset")
        return documents, metadatas
    
    # Fallback to sample data
    logger.warning("Full MedQuAD dataset not found, trying sample data...")
    medquad_file = settings.medquad_path / "sample_qa_pairs.json"
    
    if not medquad_file.exists():
        logger.warning(f"Sample MedQuAD file not found: {medquad_file}")
        return [], []
    
    with open(medquad_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    metadatas = []
    
    for item in data:
        # Combine question and answer as document
        doc_text = f"Q: {item['question']}\nA: {item['answer']}"
        documents.append(doc_text)
        
        metadatas.append({
            "source": "medquad",
            "category": item.get("category", "Unknown"),
            "type": item.get("type", "general"),
            "focus": item.get("focus", "")
        })
    
    logger.info(f"Loaded {len(documents)} MedQuAD sample documents")
    return documents, metadatas


def load_pubmed_documents():
    """Load PubMed abstracts"""
    pubmed_file = settings.pubmed_path / "sample_abstracts.json"
    
    if not pubmed_file.exists():
        logger.warning(f"PubMed file not found: {pubmed_file}")
        return [], []
    
    with open(pubmed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    metadatas = []
    
    for item in data:
        # Combine title and abstract
        doc_text = f"{item['title']}\n\n{item['abstract']}"
        documents.append(doc_text)
        
        metadatas.append({
            "source": "pubmed",
            "pmid": item.get("pmid", ""),
            "journal": item.get("journal", ""),
            "year": item.get("year", 0),
            "keywords": ",".join(item.get("keywords", []))
        })
    
    logger.info(f"Loaded {len(documents)} PubMed documents")
    return documents, metadatas


def build_vector_store():
    """Build the vector store with all documents"""
    logger.info("Building vector store")
    
    # Get retriever
    retriever = get_vector_retriever()
    
    # Load documents
    medquad_docs, medquad_meta = load_medquad_documents()
    pubmed_docs, pubmed_meta = load_pubmed_documents()
    
    # Combine all documents
    all_documents = medquad_docs + pubmed_docs
    all_metadatas = medquad_meta + pubmed_meta
    
    # Generate IDs
    ids = [f"doc_{i}" for i in range(len(all_documents))]
    
    if not all_documents:
        logger.error("No documents to add to vector store!")
        return False
    
    # Add to vector store
    logger.info(f"Adding {len(all_documents)} documents to vector store")
    success = retriever.add_documents(
        documents=all_documents,
        metadatas=all_metadatas,
        ids=ids
    )
    
    if success:
        logger.info("✓ Vector store built successfully")
        
        # Show stats
        stats = retriever.get_collection_stats()
        logger.info(f"Stats: {stats}")
    else:
        logger.error("✗ Failed to build vector store")
    
    return success


def main():
    """Main function"""
    logger.info("Starting vector store build process")
    
    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)
    
    # Build vector store
    success = build_vector_store()
    
    if success:
        logger.info("\n✓ Vector store build complete!")
        logger.info(f"Location: {settings.vector_store_path}")
    else:
        logger.error("\n✗ Vector store build failed")
        logger.info("Make sure to run 'python scripts/download_data.py' first")


if __name__ == "__main__":
    main()
