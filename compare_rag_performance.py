import sys
import os
import json
import time
from loguru import logger
import argparse
import ollama

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import system components
from backend.evaluation.evaluator import get_evaluator
from backend.models import MedicalQuery, UserMode
from backend.main import initialize_all_components, get_components
from backend.config import settings

def compare_performance(count=5, seed=42):
    """
    Compares Raw Ollama (Base Meditron) vs RAG Meditron.
    """
    print("\n" + "="*60)
    print("   Medical RAG QA - Comparison: Raw vs RAG")
    print("="*60)

    # 1. Initialize System Components
    logger.info("Initializing RAG system components...")
    try:
        initialize_all_components()
        preprocessor, agent, generator, reflector, react_agent = get_components()
        evaluator = get_evaluator()
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return

    # 2. Load Questions
    data_path = "data/medquad_processed.json"
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    
    import random
    random.seed(seed)
    # Focus on "Hallucination-prone" questions or just random ones from MedQuAD
    sample_batch = random.sample(all_data, count)

    # 3. Execution
    logger.info(f"Running comparison for {count} questions...")
    comparison_results = []

    for i, item in enumerate(sample_batch, 1):
        question = item['question']
        reference = item['answer']
        
        print(f"\n[{i}/{count}] Q: {question}")
        
        # --- A. Raw Ollama Response ---
        logger.info("   Generating RAW Ollama response...")
        raw_start = time.time()
        try:
            raw_response = ollama.generate(
                model=settings.ollama_model,
                prompt=f"Answer this medical question: {question}",
                options={'temperature': 0.7, 'num_predict': 200}
            )
            raw_answer = raw_response.get('response', '').strip()
        except Exception as e:
            logger.error(f"   Raw Ollama error: {e}")
            raw_answer = "Error"
        raw_duration = time.time() - raw_start

        # --- B. RAG Meditron Response ---
        logger.info("   Generating RAG Meditron response...")
        rag_start = time.time()
        try:
            query_obj = MedicalQuery(question=question, mode=UserMode.AUTO)
            processed_query = preprocessor.process_query(query_obj)
            rag_output = react_agent.run(processed_query, mode=UserMode.PATIENT)
            rag_answer = rag_output.answer
            evidence = rag_output.evidence_texts
        except Exception as e:
            logger.error(f"   RAG error: {e}")
            rag_answer = "Error"
            evidence = []
        rag_duration = time.time() - rag_start

        # --- C. Evaluate Both ---
        raw_metrics = evaluator.evaluate_single(
            question=question,
            generated_answer=raw_answer,
            reference_answer=reference,
            evidence_texts=[] # No evidence for raw
        )
        
        rag_metrics = evaluator.evaluate_single(
            question=question,
            generated_answer=rag_answer,
            reference_answer=reference,
            evidence_texts=evidence
        )

        comparison_results.append({
            'question': question,
            'reference': reference,
            'raw': {
                'answer': raw_answer,
                'metrics': raw_metrics,
                'time': raw_duration
            },
            'rag': {
                'answer': rag_answer,
                'metrics': rag_metrics,
                'time': rag_duration,
                'num_evidences': len(evidence)
            }
        })

    # 4. Save and Report
    output_dir = "eval_results"
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"comparison_report_{int(time.time())}.json")
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)

    # Simple CLI Summary
    print("\n" + "="*60)
    print("   COMPARISON SUMMARY")
    print("="*60)
    
    avg_raw_bleu = sum(c['raw']['metrics']['bleu'] for c in comparison_results) / count
    avg_rag_bleu = sum(c['rag']['metrics']['bleu'] for c in comparison_results) / count
    avg_raw_halluc = sum(c['raw']['metrics']['hallucination']['hallucination_rate'] for c in comparison_results) / count
    avg_rag_halluc = sum(c['rag']['metrics']['hallucination']['hallucination_rate'] for c in comparison_results) / count

    print(f"Metrics          | Raw Ollama | RAG Meditron")
    print(f"-----------------|------------|-------------")
    print(f"Avg BLEU         | {avg_raw_bleu:.4f}     | {avg_rag_bleu:.4f}")
    print(f"Avg Halluc Rate  | {avg_raw_halluc:.4f}     | {avg_rag_halluc:.4f}")
    print(f"Avg Time (s)     | {sum(c['raw']['time'] for c in comparison_results)/count:.2f}        | {sum(c['rag']['time'] for c in comparison_results)/count:.2f}")

    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    compare_performance(count=args.count)
