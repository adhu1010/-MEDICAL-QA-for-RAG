"""
Build knowledge graph from medical data
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

from backend.retrievers import get_kg_retriever
from backend.config import settings


def load_disease_ontology():
    """
    Load Disease Ontology from processed JSON
    Returns knowledge triples extracted from disease relationships
    """
    logger.info("Loading Disease Ontology")
    
    # Try to load processed Disease Ontology
    do_file = Path("../data/disease_ontology_processed.json")
    
    knowledge_triples = []
    
    if do_file.exists():
        logger.info(f"Loading Disease Ontology from {do_file}")
        with open(do_file, 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        
        logger.info(f"Loaded {len(diseases)} disease terms")
        
        # Extract triples from disease relationships (limit to prevent huge graph)
        for i, disease in enumerate(diseases[:1000]):  # Use first 1000 diseases
            disease_name = disease.get('name', '')
            
            if not disease_name:
                continue
            
            # Add definition as knowledge (truncate long definitions)
            if 'definition' in disease:
                definition = disease['definition'][:200]  # Limit definition length
                knowledge_triples.append(
                    (disease_name, "DEFINITION", definition)
                )
            
            # Add parent relationships (is_a)
            for rel in disease.get('relationships', []):
                if rel['type'] == 'is_a':
                    knowledge_triples.append(
                        (disease_name, "IS_A", rel['target'])
                    )
            
            # Add synonyms (limit to 3 per disease)
            for synonym in disease.get('synonyms', [])[:3]:
                knowledge_triples.append(
                    (disease_name, "SYNONYM", synonym)
                )
        
        logger.info(f"Extracted {len(knowledge_triples)} triples from Disease Ontology")
        return knowledge_triples
    else:
        logger.warning("Disease Ontology not found, using sample data")
        return load_sample_umls_concepts()


def load_sample_umls_concepts():
    """
    Sample medical knowledge triples (fallback if real data not available)
    """
    logger.info("Loading sample UMLS concepts")
    
    # Sample medical knowledge triples (subject, predicate, object)
    # In production, these would come from UMLS MRREL and MRCONSO files
    knowledge_triples = [
        # Drug relationships
        ("Metformin", "TREATS", "Type2Diabetes"),
        ("Metformin", "CAUSES", "Nausea"),
        ("Metformin", "CAUSES", "Diarrhea"),
        ("Metformin", "CAUSES", "StomachUpset"),
        ("Metformin", "MECHANISM", "DecreasesGlucoseProduction"),
        ("Metformin", "MECHANISM", "ImprovesInsulinSensitivity"),
        
        ("Amoxicillin", "TREATS", "BacterialSinusitis"),
        ("Amoxicillin", "DRUG_CLASS", "Penicillin"),
        ("Amoxicillin", "CAUSES", "AllergicReaction"),
        
        ("Doxycycline", "TREATS", "BacterialSinusitis"),
        ("Doxycycline", "DRUG_CLASS", "Tetracycline"),
        ("Doxycycline", "ALTERNATIVE_FOR", "Amoxicillin"),
        
        # Disease relationships
        ("Type2Diabetes", "CHARACTERIZED_BY", "Hyperglycemia"),
        ("Type2Diabetes", "CHARACTERIZED_BY", "InsulinResistance"),
        ("Type2Diabetes", "RISK_FACTOR", "Obesity"),
        ("Type2Diabetes", "RISK_FACTOR", "SedentaryLifestyle"),
        ("Type2Diabetes", "TREATED_BY", "Metformin"),
        
        ("BacterialSinusitis", "HAS_SYMPTOM", "FacialPain"),
        ("BacterialSinusitis", "HAS_SYMPTOM", "NasalCongestion"),
        ("BacterialSinusitis", "HAS_SYMPTOM", "Headache"),
        ("BacterialSinusitis", "HAS_SYMPTOM", "ThickNasalDischarge"),
        ("BacterialSinusitis", "TREATED_BY", "Amoxicillin"),
        ("BacterialSinusitis", "TREATED_BY", "Doxycycline"),
        
        # Symptom relationships
        ("Nausea", "SYMPTOM_OF", "MetforminSideEffect"),
        ("Diarrhea", "SYMPTOM_OF", "MetforminSideEffect"),
        ("FacialPain", "SYMPTOM_OF", "BacterialSinusitis"),
        ("Headache", "SYMPTOM_OF", "BacterialSinusitis"),
        
        # Additional medical knowledge
        ("Diabetes", "SUBTYPE", "Type1Diabetes"),
        ("Diabetes", "SUBTYPE", "Type2Diabetes"),
        ("Antibiotics", "INCLUDES", "Amoxicillin"),
        ("Antibiotics", "INCLUDES", "Doxycycline"),
    ]
    
    logger.info(f"Loaded {len(knowledge_triples)} knowledge triples")
    return knowledge_triples


def build_knowledge_graph():
    """Build the knowledge graph"""
    logger.info("Building knowledge graph")
    
    # Get KG retriever
    kg_retriever = get_kg_retriever()
    
    # Load knowledge triples (try Disease Ontology first, fallback to sample)
    triples = load_disease_ontology()
    
    # Add triples to KG
    for subject, predicate, obj in triples:
        kg_retriever.add_knowledge(
            subject=subject,
            predicate=predicate,
            obj=obj,
            metadata={"source": "UMLS_sample"}
        )
    
    logger.info("✓ Knowledge graph built successfully")
    
    # Show stats
    if kg_retriever.graph:
        node_count = len(kg_retriever.graph.nodes)
        edge_count = len(kg_retriever.graph.edges)
        logger.info(f"Graph stats: {node_count} nodes, {edge_count} edges")
        
        # Show sample nodes
        sample_nodes = list(kg_retriever.graph.nodes)[:5]
        logger.info(f"Sample nodes: {sample_nodes}")
    
    return True


def main():
    """Main function"""
    logger.info("Starting knowledge graph build process")
    
    # Build KG
    success = build_knowledge_graph()
    
    if success:
        logger.info("\n✓ Knowledge graph build complete!")
        logger.info("The graph is in-memory (NetworkX)")
        logger.info("For persistent storage, configure Neo4j in .env")
    else:
        logger.error("\n✗ Knowledge graph build failed")


if __name__ == "__main__":
    main()
