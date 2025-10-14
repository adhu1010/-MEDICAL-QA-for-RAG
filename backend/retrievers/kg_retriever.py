"""
Knowledge Graph retrieval using Neo4j/NetworkX
"""
from typing import List, Dict, Any, Optional
import networkx as nx
from loguru import logger

from backend.config import settings
from backend.models import RetrievedEvidence, ProcessedQuery, MedicalEntity
from backend.utils import normalize_medical_term


class KnowledgeGraphRetriever:
    """Handles retrieval from medical knowledge graph"""
    
    def __init__(self, use_neo4j: bool = False):
        """
        Initialize KG retriever
        
        Args:
            use_neo4j: If True, use Neo4j; otherwise use NetworkX
        """
        self.use_neo4j = use_neo4j
        self.graph = None
        self.neo4j_driver = None
        
        if use_neo4j:
            self._init_neo4j()
        else:
            self._init_networkx()
    
    def _init_neo4j(self):
        """Initialize Neo4j connection"""
        try:
            from neo4j import GraphDatabase
            
            self.neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            
            # Test connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            
            logger.info("Neo4j connection established")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j: {e}. Falling back to NetworkX")
            self.use_neo4j = False
            self._init_networkx()
    
    def _init_networkx(self):
        """Initialize in-memory NetworkX graph"""
        self.graph = nx.MultiDiGraph()
        logger.info("Initialized NetworkX knowledge graph")
        
        # Add sample medical knowledge (would be loaded from UMLS in production)
        self._add_sample_knowledge()
    
    def _add_sample_knowledge(self):
        """Add sample medical knowledge to NetworkX graph"""
        # Drugs
        self.graph.add_node("Metformin", type="Drug", description="Oral diabetes medication")
        self.graph.add_node("Amoxicillin", type="Drug", description="Antibiotic")
        self.graph.add_node("Doxycycline", type="Drug", description="Antibiotic")
        
        # Diseases
        self.graph.add_node("Diabetes", type="Disease", description="Metabolic disorder")
        self.graph.add_node("Sinusitis", type="Disease", description="Sinus infection")
        self.graph.add_node("Type2Diabetes", type="Disease", description="Type 2 Diabetes Mellitus")
        
        # Symptoms
        self.graph.add_node("Nausea", type="Symptom", description="Feeling of sickness")
        self.graph.add_node("Diarrhea", type="Symptom", description="Loose stools")
        self.graph.add_node("Headache", type="Symptom", description="Pain in head")
        
        # Relationships
        self.graph.add_edge("Metformin", "Type2Diabetes", relation="TREATS")
        self.graph.add_edge("Metformin", "Nausea", relation="CAUSES")
        self.graph.add_edge("Metformin", "Diarrhea", relation="CAUSES")
        
        self.graph.add_edge("Amoxicillin", "Sinusitis", relation="TREATS")
        self.graph.add_edge("Doxycycline", "Sinusitis", relation="TREATS")
        
        self.graph.add_edge("Diabetes", "Metformin", relation="TREATED_BY")
        self.graph.add_edge("Sinusitis", "Headache", relation="HAS_SYMPTOM")
        
        logger.info(f"Added sample knowledge: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
    
    def add_knowledge(
        self,
        subject: str,
        predicate: str,
        obj: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a triple to the knowledge graph
        
        Args:
            subject: Subject node
            predicate: Relationship type
            obj: Object node
            metadata: Additional metadata
        """
        if self.use_neo4j:
            self._add_to_neo4j(subject, predicate, obj, metadata)
        else:
            self._add_to_networkx(subject, predicate, obj, metadata)
    
    def _add_to_networkx(
        self,
        subject: str,
        predicate: str,
        obj: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add triple to NetworkX graph"""
        self.graph.add_node(subject)
        self.graph.add_node(obj)
        self.graph.add_edge(subject, obj, relation=predicate, **(metadata or {}))
    
    def _add_to_neo4j(
        self,
        subject: str,
        predicate: str,
        obj: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add triple to Neo4j"""
        if not self.neo4j_driver:
            return
        
        with self.neo4j_driver.session() as session:
            query = f"""
            MERGE (s:Entity {{name: $subject}})
            MERGE (o:Entity {{name: $object}})
            MERGE (s)-[r:{predicate}]->(o)
            SET r += $metadata
            """
            session.run(query, subject=subject, object=obj, metadata=metadata or {})
    
    def query_networkx(self, entities: List[MedicalEntity], top_k: int) -> List[RetrievedEvidence]:
        """Query NetworkX graph for entities"""
        evidences = []
        
        for entity in entities:
            entity_text = normalize_medical_term(entity.text)
            
            # Find matching nodes (case-insensitive)
            matching_nodes = [
                node for node in self.graph.nodes()
                if entity_text in normalize_medical_term(str(node))
            ]
            
            for node in matching_nodes:
                # Get all edges from this node
                out_edges = self.graph.out_edges(node, data=True)
                in_edges = self.graph.in_edges(node, data=True)
                
                # Create evidence from outgoing edges
                for source, target, data in out_edges:
                    relation = data.get('relation', 'RELATED_TO')
                    target_desc = self.graph.nodes.get(target, {}).get('description', '')
                    
                    content = f"{source} {relation} {target}. {target_desc}"
                    
                    evidence = RetrievedEvidence(
                        source_type="kg",
                        content=content,
                        confidence=0.9,  # High confidence for KG facts
                        metadata={
                            "subject": source,
                            "predicate": relation,
                            "object": target,
                            "entity_type": entity.entity_type
                        }
                    )
                    evidences.append(evidence)
                
                # Create evidence from incoming edges
                for source, target, data in in_edges:
                    relation = data.get('relation', 'RELATED_TO')
                    source_desc = self.graph.nodes.get(source, {}).get('description', '')
                    
                    content = f"{source} {relation} {target}. {source_desc}"
                    
                    evidence = RetrievedEvidence(
                        source_type="kg",
                        content=content,
                        confidence=0.9,
                        metadata={
                            "subject": source,
                            "predicate": relation,
                            "object": target,
                            "entity_type": entity.entity_type
                        }
                    )
                    evidences.append(evidence)
        
        # Sort by confidence and return top k
        evidences.sort(key=lambda x: x.confidence, reverse=True)
        return evidences[:top_k]
    
    def query_neo4j(self, entities: List[MedicalEntity], top_k: int) -> List[RetrievedEvidence]:
        """Query Neo4j graph for entities"""
        if not self.neo4j_driver:
            return []
        
        evidences = []
        
        with self.neo4j_driver.session() as session:
            for entity in entities:
                # Query for relationships
                query = """
                MATCH (s:Entity)-[r]->(o:Entity)
                WHERE s.name CONTAINS $entity_text OR o.name CONTAINS $entity_text
                RETURN s.name AS subject, type(r) AS predicate, o.name AS object
                LIMIT $top_k
                """
                
                results = session.run(query, entity_text=entity.text, top_k=top_k)
                
                for record in results:
                    content = f"{record['subject']} {record['predicate']} {record['object']}"
                    
                    evidence = RetrievedEvidence(
                        source_type="kg",
                        content=content,
                        confidence=0.9,
                        metadata={
                            "subject": record['subject'],
                            "predicate": record['predicate'],
                            "object": record['object']
                        }
                    )
                    evidences.append(evidence)
        
        return evidences
    
    def retrieve(self, query: ProcessedQuery, top_k: int = None) -> List[RetrievedEvidence]:
        """
        Retrieve relevant knowledge from graph
        
        Args:
            query: ProcessedQuery with extracted entities
            top_k: Number of results to return
            
        Returns:
            List of RetrievedEvidence
        """
        top_k = top_k or settings.top_k_kg
        
        if not query.entities:
            logger.info("No entities found for KG retrieval")
            return []
        
        logger.info(f"Retrieving from KG for {len(query.entities)} entities")
        
        if self.use_neo4j:
            evidences = self.query_neo4j(query.entities, top_k)
        else:
            evidences = self.query_networkx(query.entities, top_k)
        
        logger.info(f"Retrieved {len(evidences)} facts from knowledge graph")
        return evidences
    
    def close(self):
        """Close connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("Closed Neo4j connection")


# Singleton instance
_kg_retriever_instance = None


def get_kg_retriever() -> KnowledgeGraphRetriever:
    """Get or create KG retriever singleton"""
    global _kg_retriever_instance
    if _kg_retriever_instance is None:
        _kg_retriever_instance = KnowledgeGraphRetriever()
    return _kg_retriever_instance
