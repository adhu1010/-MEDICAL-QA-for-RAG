"""
Agent controller - Decision-making layer for retrieval strategy
"""
from typing import List
from loguru import logger

from backend.models import (
    ProcessedQuery, RetrievedEvidence, FusedEvidence,
    RetrievalStrategy
)
from backend.config import agent_config, settings
from backend.retrievers import get_vector_retriever, get_kg_retriever, get_sparse_retriever
from backend.utils import calculate_weighted_confidence


class AgentController:
    """
    Agentic decision layer that orchestrates retrieval strategy
    """
    
    def __init__(self):
        """Initialize agent with retrievers"""
        self.vector_retriever = get_vector_retriever()
        self.kg_retriever = get_kg_retriever()
        self.sparse_retriever = get_sparse_retriever()
        logger.info("Agent controller initialized with dense, sparse, and KG retrievers")
    
    def decide_strategy(self, query: ProcessedQuery) -> RetrievalStrategy:
        """
        Decide the optimal retrieval strategy
        
        Args:
            query: ProcessedQuery object
            
        Returns:
            RetrievalStrategy
        """
        # Use suggested strategy from preprocessing as baseline
        strategy = query.suggested_strategy
        
        logger.info(f"Agent decided on strategy: {strategy}")
        return strategy
    
    def _reciprocal_rank_fusion(
        self,
        evidences: List[RetrievedEvidence],
        k: int = 60
    ) -> List[RetrievedEvidence]:
        """
        Apply Reciprocal Rank Fusion to combine rankings from different retrievers
        
        Args:
            evidences: List of evidences from different sources
            k: RRF constant (default 60, standard value)
            
        Returns:
            Re-ranked list of evidences
        """
        # Group by source type
        source_groups = {}
        for evidence in evidences:
            source_type = evidence.source_type
            if source_type not in source_groups:
                source_groups[source_type] = []
            source_groups[source_type].append(evidence)
        
        # Sort each group by confidence (original ranking)
        for source_type in source_groups:
            source_groups[source_type].sort(key=lambda x: x.confidence, reverse=True)
        
        # Calculate RRF scores
        rrf_scores = {}
        
        for source_type, source_evidences in source_groups.items():
            for rank, evidence in enumerate(source_evidences):
                # Use content as unique identifier
                doc_id = evidence.content
                
                # RRF formula: 1 / (k + rank)
                rrf_score = 1.0 / (k + rank + 1)
                
                if doc_id in rrf_scores:
                    rrf_scores[doc_id]['score'] += rrf_score
                else:
                    rrf_scores[doc_id] = {
                        'score': rrf_score,
                        'evidence': evidence
                    }
        
        # Sort by RRF score
        ranked = sorted(rrf_scores.values(), key=lambda x: x['score'], reverse=True)
        
        # Update confidence with RRF score and return evidences
        result = []
        for item in ranked:
            evidence = item['evidence']
            evidence.confidence = item['score']
            result.append(evidence)
        
        logger.info(f"Applied RRF fusion to {len(result)} unique documents")
        return result
    
    def retrieve_with_strategy(
        self,
        query: ProcessedQuery,
        strategy: RetrievalStrategy
    ) -> List[RetrievedEvidence]:
        """
        Execute retrieval based on chosen strategy
        
        Args:
            query: ProcessedQuery
            strategy: Chosen retrieval strategy
            
        Returns:
            Combined list of evidences
        """
        evidences = []
        
        if strategy == RetrievalStrategy.KG_ONLY:
            # Only knowledge graph
            logger.info("Executing KG-only retrieval")
            evidences = self.kg_retriever.retrieve(query)
            
        elif strategy == RetrievalStrategy.VECTOR_ONLY:
            # Only dense vector search
            logger.info("Executing dense vector-only retrieval")
            evidences = self.vector_retriever.retrieve(query)
            
        elif strategy == RetrievalStrategy.SPARSE_ONLY:
            # Only sparse (BM25) search
            logger.info("Executing sparse BM25-only retrieval")
            evidences = self.sparse_retriever.retrieve(query)
            
        elif strategy == RetrievalStrategy.DENSE_SPARSE:
            # Dense + Sparse hybrid
            logger.info("Executing dense+sparse hybrid retrieval")
            vector_evidences = self.vector_retriever.retrieve(query)
            sparse_evidences = self.sparse_retriever.retrieve(query)
            evidences = vector_evidences + sparse_evidences
            
        elif strategy == RetrievalStrategy.HYBRID:
            # Legacy: KG + Dense vector
            logger.info("Executing hybrid retrieval (KG + dense)")
            kg_evidences = self.kg_retriever.retrieve(query)
            vector_evidences = self.vector_retriever.retrieve(query)
            evidences = kg_evidences + vector_evidences
            
        elif strategy == RetrievalStrategy.FULL_HYBRID:
            # All three: KG + Dense + Sparse
            logger.info("Executing full hybrid retrieval (KG + dense + sparse)")
            kg_evidences = self.kg_retriever.retrieve(query)
            vector_evidences = self.vector_retriever.retrieve(query)
            sparse_evidences = self.sparse_retriever.retrieve(query)
            evidences = kg_evidences + vector_evidences + sparse_evidences
        
        logger.info(f"Retrieved {len(evidences)} total evidences")
        return evidences
    
    def fuse_evidence(
        self,
        evidences: List[RetrievedEvidence],
        query: ProcessedQuery
    ) -> FusedEvidence:
        """
        Fuse and rank evidence from multiple sources using RRF
        
        Args:
            evidences: List of retrieved evidences
            query: Original processed query
            
        Returns:
            FusedEvidence with ranked results
        """
        if not evidences:
            return FusedEvidence(
                evidences=[],
                combined_confidence=0.0,
                fusion_method="none"
            )
        
        # Separate by source type
        kg_evidences = [e for e in evidences if e.source_type == "kg"]
        vector_evidences = [e for e in evidences if e.source_type == "vector"]
        sparse_evidences = [e for e in evidences if e.source_type == "sparse"]
        
        # Determine fusion method
        if sparse_evidences and vector_evidences:
            # Use Reciprocal Rank Fusion (RRF) for dense+sparse
            fusion_method = "reciprocal_rank_fusion"
            evidences = self._reciprocal_rank_fusion(evidences)
        else:
            # Use weighted fusion for other combinations
            fusion_method = "weighted_fusion"
            
            # Apply fusion weights
            for evidence in kg_evidences:
                evidence.confidence *= agent_config.FUSION_WEIGHT_KG
            
            for evidence in vector_evidences:
                evidence.confidence *= agent_config.FUSION_WEIGHT_VECTOR
            
            # Sparse uses default weight of 1.0
            for evidence in sparse_evidences:
                evidence.confidence *= getattr(agent_config, 'FUSION_WEIGHT_SPARSE', 0.5)
            
            # Sort by adjusted confidence
            evidences.sort(key=lambda x: x.confidence, reverse=True)
        
        # Calculate combined confidence
        if evidences:
            confidences = [e.confidence for e in evidences]
            combined_confidence = sum(confidences) / len(confidences)
        else:
            combined_confidence = 0.0
        
        logger.info(
            f"Fused evidence: {len(kg_evidences)} KG + {len(vector_evidences)} dense + "
            f"{len(sparse_evidences)} sparse, combined confidence: {combined_confidence:.2f}"
        )
        
        return FusedEvidence(
            evidences=evidences,
            combined_confidence=combined_confidence,
            fusion_method=fusion_method
        )
    
    def execute(self, query: ProcessedQuery) -> FusedEvidence:
        """
        Main execution pipeline: decide strategy -> retrieve -> fuse
        
        Args:
            query: ProcessedQuery
            
        Returns:
            FusedEvidence ready for generation
        """
        logger.info(f"Agent executing for query: {query.original_question}")
        
        # Step 1: Decide strategy
        strategy = self.decide_strategy(query)
        
        # Step 2: Retrieve with chosen strategy
        evidences = self.retrieve_with_strategy(query, strategy)
        
        # Step 3: Fuse evidence
        fused = self.fuse_evidence(evidences, query)
        
        logger.info(f"Agent execution complete with {len(fused.evidences)} evidences")
        
        return fused


# Singleton instance
_agent_instance = None


def get_agent_controller() -> AgentController:
    """Get or create AgentController singleton"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentController()
    return _agent_instance
