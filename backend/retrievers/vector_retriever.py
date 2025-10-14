"""
Vector-based retrieval using ChromaDB and BioBERT embeddings
"""
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from loguru import logger

from backend.config import settings
from backend.models import RetrievedEvidence, ProcessedQuery
from backend.utils import split_into_chunks, deduplicate_results


class VectorRetriever:
    """Handles vector-based document retrieval"""
    
    def __init__(
        self,
        embedding_model: str = None,
        collection_name: str = "medical_documents"
    ):
        """
        Initialize vector retriever
        
        Args:
            embedding_model: HuggingFace model name for embeddings
            collection_name: ChromaDB collection name
        """
        self.embedding_model_name = embedding_model or settings.embedding_model
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load {self.embedding_model_name}, using fallback")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with persistence
        try:
            # Use PersistentClient for newer ChromaDB versions (>= 0.4.0)
            if hasattr(chromadb, 'PersistentClient'):
                self.chroma_client = chromadb.PersistentClient(
                    path=str(settings.vector_store_path)
                )
                logger.info(f"ChromaDB initialized with PersistentClient at {settings.vector_store_path}")
            else:
                # Fallback for older versions
                self.chroma_client = chromadb.Client(
                    chromadb.Settings(
                        chroma_db_impl="duckdb+parquet",
                        persist_directory=str(settings.vector_store_path),
                        anonymized_telemetry=False
                    )
                )
                logger.info(f"ChromaDB initialized with Client at {settings.vector_store_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
        
        # Get or create collection with cosine similarity
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity instead of L2
            )
            logger.info(f"Loaded ChromaDB collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            self.collection = None
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to vector store with automatic batching
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
            
        Returns:
            Success boolean
        """
        if not self.collection:
            logger.error("ChromaDB collection not initialized")
            return False
        
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            # Prepare metadatas
            if metadatas is None:
                metadatas = [{} for _ in documents]
            
            # ChromaDB has a batch size limit (~5461), so process in batches
            BATCH_SIZE = 5000
            total_docs = len(documents)
            
            logger.info(f"Adding {total_docs} documents in batches of {BATCH_SIZE}")
            
            for start_idx in range(0, total_docs, BATCH_SIZE):
                end_idx = min(start_idx + BATCH_SIZE, total_docs)
                batch_docs = documents[start_idx:end_idx]
                batch_ids = ids[start_idx:end_idx]
                batch_metadata = metadatas[start_idx:end_idx]
                
                # Generate embeddings for batch
                logger.info(f"  Processing batch {start_idx//BATCH_SIZE + 1}: documents {start_idx+1} to {end_idx}")
                batch_embeddings = [self.embed_text(doc) for doc in batch_docs]
                
                # Add batch to collection
                self.collection.add(
                    embeddings=batch_embeddings,
                    documents=batch_docs,
                    metadatas=batch_metadata,
                    ids=batch_ids
                )
                
                logger.info(f"  ✓ Batch {start_idx//BATCH_SIZE + 1} complete: {len(batch_docs)} documents added")
            
            logger.info(f"✓ Successfully added all {total_docs} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def retrieve(
        self,
        query: ProcessedQuery,
        top_k: int = None
    ) -> List[RetrievedEvidence]:
        """
        Retrieve relevant documents for query
        
        Args:
            query: ProcessedQuery object
            top_k: Number of top results to return
            
        Returns:
            List of RetrievedEvidence
        """
        if not self.collection:
            logger.warning("ChromaDB collection not available")
            return []
        
        top_k = top_k or settings.top_k_vector
        
        try:
            # Generate query embedding
            query_embedding = self.embed_text(query.normalized_question)
            
            if not query_embedding:
                return []
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to RetrievedEvidence
            evidences = []
            
            if results and results['documents']:
                logger.info(f"Raw retrieval found {len(results['documents'][0])} documents")
                for i, doc in enumerate(results['documents'][0]):
                    # Convert distance to similarity (1 - distance)
                    distance = results['distances'][0][i]
                    confidence = max(0.0, 1.0 - distance)
                    
                    logger.info(f"  Doc {i}: distance={distance:.4f}, confidence={confidence:.4f}, threshold={settings.similarity_threshold}")
                    
                    # Only include if above threshold
                    if confidence >= settings.similarity_threshold:
                        metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                        
                        evidence = RetrievedEvidence(
                            source_type="vector",
                            content=doc,
                            confidence=confidence,
                            metadata=metadata
                        )
                        evidences.append(evidence)
            
            logger.info(f"Retrieved {len(evidences)} documents from vector store")
            return evidences
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.collection:
            return {"error": "Collection not initialized"}
        
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection.name,
                "document_count": count,
                "embedding_model": self.embedding_model_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


# Singleton instance
_retriever_instance = None


def get_vector_retriever() -> VectorRetriever:
    """Get or create VectorRetriever singleton"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = VectorRetriever()
    return _retriever_instance
