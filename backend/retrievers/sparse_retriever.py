"""
Sparse retrieval using BM25 for keyword-based matching
"""
from typing import List, Dict, Any, Optional
import pickle
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi
from loguru import logger

from backend.config import settings
from backend.models import RetrievedEvidence, ProcessedQuery
from backend.utils import normalize_medical_term


class SparseRetriever:
    """Handles sparse (keyword-based) document retrieval using BM25"""
    
    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize sparse retriever
        
        Args:
            index_path: Path to save/load BM25 index
        """
        self.index_path = index_path or settings.data_dir / "bm25_index.pkl"
        self.bm25 = None
        self.documents = []
        self.metadatas = []
        self.ids = []
        
        # Try to load existing index
        if self.index_path.exists():
            self._load_index()
        else:
            logger.info("No existing BM25 index found. Will create on first build.")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Simple tokenization: lowercase, split on whitespace and punctuation
        # For medical text, we keep hyphens (e.g., "Type-2")
        text = text.lower()
        
        # Replace punctuation except hyphens with spaces
        for char in ".,;:!?()[]{}\"'`@#$%^&*+=<>/\\|~":
            text = text.replace(char, " ")
        
        # Split and filter
        tokens = [t.strip() for t in text.split() if len(t.strip()) > 1]
        
        return tokens
    
    def build_index(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Build BM25 index from documents
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            Success boolean
        """
        try:
            logger.info(f"Building BM25 index for {len(documents)} documents")
            
            # Store documents and metadata
            self.documents = documents
            self.metadatas = metadatas or [{} for _ in documents]
            self.ids = ids or [f"doc_{i}" for i in range(len(documents))]
            
            # Tokenize all documents
            logger.info("Tokenizing documents...")
            tokenized_corpus = [self._tokenize(doc) for doc in documents]
            
            # Build BM25 index
            logger.info("Building BM25 index...")
            self.bm25 = BM25Okapi(tokenized_corpus)
            
            # Save index
            self._save_index()
            
            logger.info(f"✓ BM25 index built successfully for {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            return False
    
    def _save_index(self):
        """Save BM25 index to disk"""
        try:
            # Ensure directory exists
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save index and associated data
            index_data = {
                'bm25': self.bm25,
                'documents': self.documents,
                'metadatas': self.metadatas,
                'ids': self.ids
            }
            
            with open(self.index_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info(f"BM25 index saved to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error saving BM25 index: {e}")
    
    def _load_index(self):
        """Load BM25 index from disk"""
        try:
            logger.info(f"Loading BM25 index from {self.index_path}")
            
            with open(self.index_path, 'rb') as f:
                index_data = pickle.load(f)
            
            self.bm25 = index_data['bm25']
            self.documents = index_data['documents']
            self.metadatas = index_data['metadatas']
            self.ids = index_data['ids']
            
            logger.info(f"✓ BM25 index loaded: {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error loading BM25 index: {e}")
            self.bm25 = None
    
    def retrieve(
        self,
        query: ProcessedQuery,
        top_k: int = None
    ) -> List[RetrievedEvidence]:
        """
        Retrieve relevant documents using BM25
        
        Args:
            query: ProcessedQuery object
            top_k: Number of top results to return
            
        Returns:
            List of RetrievedEvidence
        """
        if not self.bm25:
            logger.warning("BM25 index not available")
            return []
        
        top_k = top_k or settings.top_k_vector
        
        try:
            # Tokenize query
            query_tokens = self._tokenize(query.normalized_question)
            
            if not query_tokens:
                return []
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Convert to RetrievedEvidence
            evidences = []
            
            # Normalize scores to [0, 1] range
            max_score = scores[top_indices[0]] if len(top_indices) > 0 else 1.0
            
            for idx in top_indices:
                score = scores[idx]
                
                # Skip if score is 0 (no matching terms)
                if score <= 0:
                    continue
                
                # Normalize confidence
                confidence = min(1.0, score / max_score) if max_score > 0 else 0.0
                
                # Only include if above threshold
                if confidence >= settings.similarity_threshold:
                    evidence = RetrievedEvidence(
                        source_type="sparse",
                        content=self.documents[idx],
                        confidence=confidence,
                        metadata={
                            **self.metadatas[idx],
                            'bm25_score': float(score),
                            'doc_id': self.ids[idx]
                        }
                    )
                    evidences.append(evidence)
            
            logger.info(f"Retrieved {len(evidences)} documents from BM25 (threshold: {settings.similarity_threshold})")
            return evidences
            
        except Exception as e:
            logger.error(f"Error during BM25 retrieval: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the BM25 index"""
        if not self.bm25:
            return {"error": "Index not initialized"}
        
        return {
            "index_type": "BM25Okapi",
            "document_count": len(self.documents),
            "index_path": str(self.index_path),
            "index_size_mb": self.index_path.stat().st_size / (1024 * 1024) if self.index_path.exists() else 0
        }


# Singleton instance
_sparse_retriever_instance = None


def get_sparse_retriever() -> SparseRetriever:
    """Get or create SparseRetriever singleton"""
    global _sparse_retriever_instance
    if _sparse_retriever_instance is None:
        _sparse_retriever_instance = SparseRetriever()
    return _sparse_retriever_instance
