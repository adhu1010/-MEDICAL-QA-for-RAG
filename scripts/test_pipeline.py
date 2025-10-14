"""
Test script to verify the complete pipeline
"""
import sys
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    class SimpleLogger:
        def info(self, msg): print(msg)
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    logger = SimpleLogger()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import MedicalQuery, UserMode
from backend.preprocessing import get_query_preprocessor
from backend.agents import get_agent_controller
from backend.generators import get_answer_generator
from backend.safety import get_safety_reflector


def test_pipeline():
    """Test the complete QA pipeline"""
    logger.info("="*60)
    logger.info("TESTING MEDICAL RAG QA PIPELINE")
    logger.info("="*60)
    
    # Initialize components
    logger.info("\n1️⃣ Initializing components...")
    preprocessor = get_query_preprocessor()
    agent = get_agent_controller()
    generator = get_answer_generator()
    reflector = get_safety_reflector()
    logger.info("✓ All components initialized")
    
    # Test question
    test_question = "What are the side effects of Metformin?"
    logger.info(f"\n2️⃣ Test Question: {test_question}")
    
    # Create query
    query = MedicalQuery(
        question=test_question,
        mode=UserMode.PATIENT
    )
    
    # Preprocess
    logger.info("\n3️⃣ Preprocessing query...")
    processed = preprocessor.process_query(query)
    logger.info(f"   - Query type: {processed.query_type}")
    logger.info(f"   - Strategy: {processed.suggested_strategy}")
    logger.info(f"   - Entities found: {len(processed.entities)}")
    for entity in processed.entities:
        logger.info(f"     • {entity.text} ({entity.entity_type})")
    
    # Retrieve
    logger.info("\n4️⃣ Retrieving evidence...")
    fused_evidence = agent.execute(processed)
    logger.info(f"   - Evidence count: {len(fused_evidence.evidences)}")
    logger.info(f"   - Confidence: {fused_evidence.combined_confidence:.2f}")
    logger.info("   - Top evidences:")
    for i, ev in enumerate(fused_evidence.evidences[:3], 1):
        logger.info(f"     {i}. [{ev.source_type}] {ev.content[:100]}...")
    
    # Generate
    logger.info("\n5️⃣ Generating answer...")
    generated = generator.generate(processed, fused_evidence, UserMode.PATIENT)
    logger.info(f"   - Answer length: {len(generated.answer)} chars")
    logger.info(f"   - Confidence: {generated.confidence:.2f}")
    
    # Safety check
    logger.info("\n6️⃣ Safety validation...")
    evidence_texts = [ev.content for ev in fused_evidence.evidences]
    safety = reflector.validate(generated, evidence_texts, is_patient_mode=True)
    logger.info(f"   - Is safe: {safety.is_safe}")
    if safety.issues:
        logger.info(f"   - Issues: {safety.issues}")
    if safety.suggestions:
        logger.info(f"   - Suggestions: {safety.suggestions}")
    
    # Final answer
    logger.info("\n" + "="*60)
    logger.info("FINAL ANSWER")
    logger.info("="*60)
    logger.info(generated.answer)
    logger.info("\n" + "="*60)
    logger.info(f"Sources: {', '.join(generated.sources)}")
    logger.info("="*60)
    
    return True


def test_multiple_questions():
    """Test with multiple questions"""
    logger.info("\n\n" + "="*60)
    logger.info("TESTING MULTIPLE QUESTIONS")
    logger.info("="*60)
    
    questions = [
        "What are the side effects of Metformin?",
        "What is Type 2 Diabetes?",
        "What is the best antibiotic for sinus infection?",
        "How does Metformin work?"
    ]
    
    preprocessor = get_query_preprocessor()
    agent = get_agent_controller()
    
    for i, question in enumerate(questions, 1):
        logger.info(f"\n{i}. Question: {question}")
        
        query = MedicalQuery(question=question, mode=UserMode.PATIENT)
        processed = preprocessor.process_query(query)
        fused = agent.execute(processed)
        
        logger.info(f"   Type: {processed.query_type.value}")
        logger.info(f"   Strategy: {processed.suggested_strategy.value}")
        logger.info(f"   Evidence: {len(fused.evidences)} items")
        logger.info(f"   Confidence: {fused.combined_confidence:.2f}")


def main():
    """Main test function"""
    try:
        # Test single pipeline
        success = test_pipeline()
        
        if success:
            logger.info("\n✓ Pipeline test PASSED")
            
            # Test multiple questions
            test_multiple_questions()
            
            logger.info("\n\n" + "="*60)
            logger.info("ALL TESTS COMPLETED SUCCESSFULLY")
            logger.info("="*60)
        else:
            logger.error("\n✗ Pipeline test FAILED")
            
    except Exception as e:
        logger.error(f"\n✗ Error during testing: {e}", exc_info=True)
        logger.error("\nMake sure to run setup first:")
        logger.error("  python scripts/download_data.py")
        logger.error("  python scripts/build_vector_store.py")
        logger.error("  python scripts/build_knowledge_graph.py")


if __name__ == "__main__":
    main()
