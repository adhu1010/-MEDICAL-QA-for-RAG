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

    def __init__(self, use_neo4j: Optional[bool] = None):
        """
        Initialize KG retriever

        Args:
            use_neo4j: If True, use Neo4j; if False, use NetworkX; if None, read from settings.NEO4J_ENABLED
        """
        # Determine backend from argument or settings
        if use_neo4j is None:
            self.use_neo4j = getattr(settings, "neo4j_enabled", False)
        else:
            self.use_neo4j = use_neo4j
        self.graph = None
        self.neo4j_driver = None

        if self.use_neo4j:
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
            logger.warning(
                f"Failed to connect to Neo4j: {e}. Falling back to NetworkX")
            self.use_neo4j = False
            self._init_networkx()

    def _init_networkx(self):
        """Initialize in-memory NetworkX graph"""
        self.graph = nx.MultiDiGraph()
        logger.info("Initialized NetworkX knowledge graph")

        # Add sample medical knowledge (would be loaded from UMLS in production)
        self._add_sample_knowledge()

    def _add_sample_knowledge(self):
        """Add comprehensive medical knowledge to NetworkX graph - Common conditions & facts"""

        # === DIABETES (Type 1 & Type 2) ===
        self.graph.add_node("Diabetes", type="Disease",
                            description="Metabolic disorder affecting blood sugar")
        self.graph.add_node("Type1Diabetes", type="Disease",
                            description="Autoimmune diabetes requiring insulin")
        self.graph.add_node("Type2Diabetes", type="Disease",
                            description="Type 2 Diabetes Mellitus")
        self.graph.add_node("GestationalDiabetes", type="Disease",
                            description="Diabetes during pregnancy")

        # Diabetes Symptoms
        self.graph.add_node("IncreasedThirst", type="Symptom",
                            description="Excessive thirst (polydipsia)")
        self.graph.add_node("FrequentUrination", type="Symptom",
                            description="Increased urination (polyuria)")
        self.graph.add_node("UnexplainedWeightLoss", type="Symptom",
                            description="Weight loss without trying")
        self.graph.add_node("BlurredVision", type="Symptom",
                            description="Vision problems")
        self.graph.add_node("Fatigue", type="Symptom",
                            description="Extreme tiredness")
        self.graph.add_node("SlowHealingSores", type="Symptom",
                            description="Wounds heal slowly")

        # Diabetes Treatments
        self.graph.add_node("Insulin", type="Drug",
                            description="Hormone regulating blood sugar")
        self.graph.add_node("Metformin", type="Drug",
                            description="Oral diabetes medication")

        # Diabetes Risk Factors
        self.graph.add_node("Obesity", type="RiskFactor",
                            description="Excess body weight")
        self.graph.add_node("FamilyHistory", type="RiskFactor",
                            description="Genetic predisposition")
        self.graph.add_node(
            "PhysicalInactivity", type="RiskFactor", description="Sedentary lifestyle")

        # Diabetes Complications
        self.graph.add_node("DiabeticRetinopathy", type="Complication",
                            description="Eye damage from diabetes")
        self.graph.add_node("DiabeticNeuropathy", type="Complication",
                            description="Nerve damage from diabetes")
        self.graph.add_node("KidneyDisease", type="Complication",
                            description="Diabetic nephropathy")

        # Diabetes Relationships
        self.graph.add_edge("Diabetes", "IncreasedThirst",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge("Diabetes", "FrequentUrination",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge("Diabetes", "BlurredVision",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "Type1Diabetes", "IncreasedThirst", relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "Type1Diabetes", "UnexplainedWeightLoss", relation="HAS_SYMPTOM")
        self.graph.add_edge("Type1Diabetes", "Fatigue", relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "Type2Diabetes", "IncreasedThirst", relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "Type2Diabetes", "FrequentUrination", relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "Type2Diabetes", "SlowHealingSores", relation="HAS_SYMPTOM")

        self.graph.add_edge("Type1Diabetes", "Insulin", relation="TREATED_BY")
        self.graph.add_edge("Type2Diabetes", "Metformin",
                            relation="TREATED_BY")
        self.graph.add_edge("Metformin", "Type2Diabetes", relation="TREATS")
        self.graph.add_edge("Insulin", "Type1Diabetes", relation="TREATS")

        self.graph.add_edge("Type2Diabetes", "Obesity", relation="RISK_FACTOR")
        self.graph.add_edge(
            "Type2Diabetes", "PhysicalInactivity", relation="RISK_FACTOR")
        self.graph.add_edge("Diabetes", "FamilyHistory",
                            relation="RISK_FACTOR")

        self.graph.add_edge("Diabetes", "DiabeticRetinopathy",
                            relation="COMPLICATION")
        self.graph.add_edge("Diabetes", "DiabeticNeuropathy",
                            relation="COMPLICATION")
        self.graph.add_edge("Diabetes", "KidneyDisease",
                            relation="COMPLICATION")

        # === HYPERTENSION (High Blood Pressure) ===
        self.graph.add_node("Hypertension", type="Disease",
                            description="High blood pressure")
        self.graph.add_node("HighBloodPressure", type="Disease",
                            description="Elevated blood pressure")

        # Hypertension Symptoms
        self.graph.add_node("Headache", type="Symptom",
                            description="Pain in head")
        self.graph.add_node("Dizziness", type="Symptom",
                            description="Feeling lightheaded")
        self.graph.add_node("Nosebleeds", type="Symptom",
                            description="Bleeding from nose")
        self.graph.add_node("ShortnessOfBreath", type="Symptom",
                            description="Difficulty breathing")

        # Hypertension Treatments
        self.graph.add_node("Lisinopril", type="Drug",
                            description="ACE inhibitor for hypertension")
        self.graph.add_node("Amlodipine", type="Drug",
                            description="Calcium channel blocker")

        # Hypertension Relationships
        self.graph.add_edge("Hypertension", "Headache", relation="HAS_SYMPTOM")
        self.graph.add_edge("Hypertension", "Dizziness",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "Hypertension", "ShortnessOfBreath", relation="HAS_SYMPTOM")
        self.graph.add_edge("Hypertension", "Lisinopril",
                            relation="TREATED_BY")
        self.graph.add_edge("Hypertension", "Amlodipine",
                            relation="TREATED_BY")
        self.graph.add_edge("Obesity", "Hypertension", relation="CAUSES")

        # === ASTHMA ===
        self.graph.add_node("Asthma", type="Disease",
                            description="Chronic lung condition")
        self.graph.add_node("Wheezing", type="Symptom",
                            description="Whistling sound when breathing")
        self.graph.add_node("ChestTightness", type="Symptom",
                            description="Tight feeling in chest")
        self.graph.add_node("Coughing", type="Symptom",
                            description="Persistent cough")
        self.graph.add_node("Albuterol", type="Drug",
                            description="Bronchodilator inhaler")

        self.graph.add_edge("Asthma", "Wheezing", relation="HAS_SYMPTOM")
        self.graph.add_edge("Asthma", "ShortnessOfBreath",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge("Asthma", "ChestTightness", relation="HAS_SYMPTOM")
        self.graph.add_edge("Asthma", "Coughing", relation="HAS_SYMPTOM")
        self.graph.add_edge("Asthma", "Albuterol", relation="TREATED_BY")

        # === INFLUENZA (Flu) ===
        self.graph.add_node("Influenza", type="Disease",
                            description="Viral respiratory infection")
        self.graph.add_node("Flu", type="Disease",
                            description="Influenza virus infection")
        self.graph.add_node("Fever", type="Symptom",
                            description="Elevated body temperature")
        self.graph.add_node("BodyAches", type="Symptom",
                            description="Muscle pain")
        self.graph.add_node("Chills", type="Symptom",
                            description="Feeling cold")
        self.graph.add_node("SoreThroat", type="Symptom",
                            description="Throat pain")

        self.graph.add_edge("Influenza", "Fever", relation="HAS_SYMPTOM")
        self.graph.add_edge("Influenza", "BodyAches", relation="HAS_SYMPTOM")
        self.graph.add_edge("Influenza", "Chills", relation="HAS_SYMPTOM")
        self.graph.add_edge("Influenza", "Coughing", relation="HAS_SYMPTOM")
        self.graph.add_edge("Influenza", "SoreThroat", relation="HAS_SYMPTOM")
        self.graph.add_edge("Influenza", "Fatigue", relation="HAS_SYMPTOM")

        # === DEPRESSION ===
        self.graph.add_node("Depression", type="Disease",
                            description="Mental health disorder")
        self.graph.add_node("Sadness", type="Symptom",
                            description="Persistent low mood")
        self.graph.add_node("LossOfInterest", type="Symptom",
                            description="Anhedonia")
        self.graph.add_node("SleepProblems", type="Symptom",
                            description="Insomnia or hypersomnia")
        self.graph.add_node("Sertraline", type="Drug",
                            description="SSRI antidepressant")

        self.graph.add_edge("Depression", "Sadness", relation="HAS_SYMPTOM")
        self.graph.add_edge("Depression", "LossOfInterest",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge("Depression", "Fatigue", relation="HAS_SYMPTOM")
        self.graph.add_edge("Depression", "SleepProblems",
                            relation="HAS_SYMPTOM")
        self.graph.add_edge("Depression", "Sertraline", relation="TREATED_BY")

        # === HEART DISEASE ===
        self.graph.add_node("CoronaryArteryDisease", type="Disease",
                            description="Narrowing of heart arteries")
        self.graph.add_node("HeartAttack", type="Disease",
                            description="Myocardial infarction")
        self.graph.add_node("ChestPain", type="Symptom",
                            description="Angina or heart pain")
        self.graph.add_node("Aspirin", type="Drug",
                            description="Blood thinner")

        self.graph.add_edge("CoronaryArteryDisease",
                            "ChestPain", relation="HAS_SYMPTOM")
        self.graph.add_edge("HeartAttack", "ChestPain", relation="HAS_SYMPTOM")
        self.graph.add_edge(
            "HeartAttack", "ShortnessOfBreath", relation="HAS_SYMPTOM")
        self.graph.add_edge("CoronaryArteryDisease",
                            "Aspirin", relation="TREATED_BY")

        # === COMMON INFECTIONS ===
        self.graph.add_node("Sinusitis", type="Disease",
                            description="Sinus infection")
        self.graph.add_node("Amoxicillin", type="Drug",
                            description="Antibiotic")
        self.graph.add_node("Doxycycline", type="Drug",
                            description="Antibiotic")
        self.graph.add_node("Nausea", type="Symptom",
                            description="Feeling of sickness")
        self.graph.add_node("Diarrhea", type="Symptom",
                            description="Loose stools")

        self.graph.add_edge("Sinusitis", "Headache", relation="HAS_SYMPTOM")
        self.graph.add_edge("Sinusitis", "Amoxicillin", relation="TREATED_BY")
        self.graph.add_edge("Sinusitis", "Doxycycline", relation="TREATED_BY")
        self.graph.add_edge("Metformin", "Nausea", relation="CAUSES")
        self.graph.add_edge("Metformin", "Diarrhea", relation="CAUSES")

        logger.info(
            f"Added comprehensive knowledge: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")

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
        self.graph.add_edge(
            subject, obj, relation=predicate, **(metadata or {}))

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
            session.run(query, subject=subject, object=obj,
                        metadata=metadata or {})

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
                    target_desc = self.graph.nodes.get(
                        target, {}).get('description', '')

                    content = f"{source} {relation} {target}. {target_desc}"

                    evidence = RetrievedEvidence(
                        source_type="kg",
                        content=content,
                        confidence=0.9,  # High confidence for KG facts
                        metadata={
                            "source": "knowledge_graph",
                            "category": f"Disease Ontology ({relation})",
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
                    source_desc = self.graph.nodes.get(
                        source, {}).get('description', '')

                    content = f"{source} {relation} {target}. {source_desc}"

                    evidence = RetrievedEvidence(
                        source_type="kg",
                        content=content,
                        confidence=0.9,
                        metadata={
                            "source": "knowledge_graph",
                            "category": f"Disease Ontology ({relation})",
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

                results = session.run(
                    query, entity_text=entity.text, top_k=top_k)

                for record in results:
                    content = f"{record['subject']} {record['predicate']} {record['object']}"

                    evidence = RetrievedEvidence(
                        source_type="kg",
                        content=content,
                        confidence=0.9,
                        metadata={
                            "source": "knowledge_graph",
                            "category": f"Neo4j ({record['predicate']})",
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
