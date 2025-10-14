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
from backend.retrievers import get_vector_retriever, get_kg_retriever
from backend.utils import calculate_weighted_confidence


class AgentController:
    """
    Agentic decision layer that orchestrates retrieval strategy
    """
    
    def __init__(self):
        """Initialize agent with retrievers"""
        self.vector_retriever = get_vector_retriever()
        self.kg_retriever = get_kg_retriever()
        logger.info("Agent controller initialized")
    
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
            # Only vector search
            logger.info("Executing vector-only retrieval")
            evidences = self.vector_retriever.retrieve(query)
            
        elif strategy == RetrievalStrategy.HYBRID:
            # Both KG and vector
            logger.info("Executing hybrid retrieval")
            kg_evidences = self.kg_retriever.retrieve(query)
            vector_evidences = self.vector_retriever.retrieve(query)
            evidences = kg_evidences + vector_evidences
        
        logger.info(f"Retrieved {len(evidences)} total evidences")
        return evidences
    
    def fuse_evidence(
        self,
        evidences: List[RetrievedEvidence],
        query: ProcessedQuery
    ) -> FusedEvidence:
        """
        Fuse and rank evidence from multiple sources
        
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
        
        # Calculate weighted scores
        fusion_method = "weighted_fusion"
        
        # Apply fusion weights
        for evidence in kg_evidences:
            evidence.confidence *= agent_config.FUSION_WEIGHT_KG
        
        for evidence in vector_evidences:
            evidence.confidence *= agent_config.FUSION_WEIGHT_VECTOR
        
        # Sort by adjusted confidence
        evidences.sort(key=lambda x: x.confidence, reverse=True)
        
        # Calculate combined confidence
        if evidences:
            confidences = [e.confidence for e in evidences]
            combined_confidence = sum(confidences) / len(confidences)
        else:
            combined_confidence = 0.0
        
        logger.info(
            f"Fused evidence: {len(kg_evidences)} KG + {len(vector_evidences)} vector, "
            f"combined confidence: {combined_confidence:.2f}"
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
