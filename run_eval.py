import sys
import os
import json
import time
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import system components
from backend.evaluation.evaluator import get_evaluator
from backend.models import MedicalQuery, UserMode
from backend.main import initialize_all_components, get_components

def run_evaluation():
    """
    Evaluates the Medical RAG QA system using specific hallucination test cases.
    It measures BLEU, ROUGE, Faithfulness, and Hallucination rates.
    """
    print("\n" + "="*60)
    print("   Medical RAG QA System - Model Evaluation")
    print("="*60)

    # 1. Initialize System Components
    logger.info("Initializing system components (Models, Retrievers, Agents)...")
    start_time = time.time()
    try:
        initialize_all_components()
        preprocessor, agent, generator, reflector, react_agent = get_components()
        evaluator = get_evaluator()
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return

    init_duration = time.time() - start_time
    logger.info(f"System ready in {init_duration:.2f} seconds.")

    # 2. Define High-Value Test Cases (from HALLUCINATION_TEST_CASES.md)
    # These questions are designed to trigger hallucinations in base models but
    # should be handled correctly by the RAG system.
    test_cases = [
        {
            "question": "What is the estimated prevalence of Imerslund-Grasbeck syndrome in Finland and Norway?",
            "reference_answer": "Imerslund-Grasbeck syndrome is estimated to affect 1 in 200,000 people in Finland and Norway.",
            "mode": UserMode.AUTO
        },
        {
            "question": "What is the estimated prevalence of the X-linked recessive type of Anhidrotic Ectodermal Dysplasia with Immune Deficiency (EDA-ID)?",
            "reference_answer": "The prevalence of the X-linked recessive type of EDA-ID is estimated to be 1 in 250,000 individuals.",
            "mode": UserMode.AUTO
        },
        {
            "question": "What is the estimated prevalence of Complement Component 2 Deficiency in Western countries?",
            "reference_answer": "In Western countries, complement component 2 deficiency is estimated to affect 1 in 20,000 individuals.",
            "mode": UserMode.AUTO
        },
        {
            "question": "What are the common symptoms of diabetes?",
            "reference_answer": "Common symptoms of diabetes include increased thirst, frequent urination, unexplained weight loss, fatigue, blurred vision, and slow-healing sores.",
            "mode": UserMode.PATIENT
        }
    ]

    # 3. Execute Queries and Collect Results
    logger.info(f"Starting evaluation of {len(test_cases)} test cases...")
    eval_start_time = time.time()
    
    evaluation_results = []
    
    for i, case in enumerate(test_cases, 1):
        question = case['question']
        logger.info(f"[{i}/{len(test_cases)}] Query: {question}")
        
        try:
            # Step A: Preprocess Query
            query_obj = MedicalQuery(question=question, mode=case['mode'])
            processed_query = preprocessor.process_query(query_obj)
            
            # Use detected mode if AUTO
            run_mode = case['mode']
            if run_mode == UserMode.AUTO:
                run_mode = processed_query.detected_mode
            
            # Step B: Run Agent Pipeline
            # This follows the same logic as backend/main.py:ask_medical_question
            logger.info(f"   Generating answer (Mode: {run_mode.value})...")
            gen_start = time.time()
            generated_answer = react_agent.run(processed_query, mode=run_mode)
            gen_duration = time.time() - gen_start
            
            # Step C: Run Evaluation Metrics
            logger.info(f"   Calculating metrics...")
            metrics = evaluator.evaluate_single(
                question=question,
                generated_answer=generated_answer.answer,
                reference_answer=case['reference_answer'],
                evidence_texts=generated_answer.evidence_texts or []
            )
            
            # Enrich metrics with context
            metrics['generated_answer'] = generated_answer.answer
            metrics['reference_answer'] = case['reference_answer']
            metrics['confidence'] = generated_answer.confidence
            metrics['generation_time'] = gen_duration
            metrics['agent_type'] = generated_answer.metadata.get('agent_type', 'unknown')
            metrics['num_evidences'] = len(generated_answer.evidence_texts) if generated_answer.evidence_texts else 0
            
            evaluation_results.append(metrics)
            
            logger.info(f"   ✓ Done. BLEU: {metrics['bleu']:.4f} | Faithfulness: {metrics['faithfulness']:.4f}")
            
        except Exception as e:
            logger.error(f"   ✗ Error evaluating test case {i}: {e}")

    eval_duration = time.time() - eval_start_time
    
    # 4. Aggregate and display summary
    if not evaluation_results:
        logger.error("No test cases were successfully evaluated.")
        return

    summary = evaluator.evaluate_batch(evaluation_results)
    
    # Add extra metadata to summary
    summary['total_eval_time'] = eval_duration
    summary['avg_generation_time'] = sum(r['generation_time'] for r in evaluation_results) / len(evaluation_results)
    
    evaluator.print_summary(summary)
    
    # 5. Save Report
    output_dir = "eval_results"
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"evaluation_report_{int(time.time())}.json")
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    # Also save a summary text file
    summary_txt_path = os.path.join(output_dir, "latest_summary.txt")
    with open(summary_txt_path, "w") as f:
        f.write("MEDICAL RAG QA EVALUATION SUMMARY\n")
        f.write("="*40 + "\n")
        f.write(f"Timestamp: {time.ctime()}\n")
        f.write(f"Test Cases: {summary['num_cases']}\n")
        f.write(f"Avg BLEU: {summary['avg_bleu']:.4f}\n")
        f.write(f"Avg ROUGE-L: {summary['avg_rougeL']:.4f}\n")
        f.write(f"Avg Faithfulness: {summary['avg_faithfulness']:.4f}\n")
        f.write(f"Avg Hallucination Rate: {summary['avg_hallucination_rate']:.4f}\n")
        f.write(f"Avg Gen Time: {summary['avg_generation_time']:.2f}s\n")
        
    print(f"\n✅ Evaluation complete. Detailed report saved to: {report_path}")
    print(f"📄 Summary saved to: {summary_txt_path}")

if __name__ == "__main__":
    run_evaluation()
