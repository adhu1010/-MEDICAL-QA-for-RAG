import sys
import os
import json
import time
import random
from loguru import logger
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import system components
from backend.evaluation.evaluator import get_evaluator
from backend.models import MedicalQuery, UserMode
from backend.main import initialize_all_components, get_components

def run_batch_evaluation(count=100, seed=42):
    """
    Evaluates the Medical RAG QA system using a batch of questions from MedQuAD.
    """
    print("\n" + "="*60)
    print(f"   Medical RAG QA System - Batch Evaluation ({count} questions)")
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

    logger.info(f"System ready in {time.time() - start_time:.2f} seconds.")

    # 2. Load Questions from MedQuAD
    data_path = "data/medquad_processed.json"
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}. Please process MedQuAD first.")
        return

    logger.info(f"Loading questions from {data_path}...")
    with open(data_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    
    logger.info(f"Total available questions: {len(all_data)}")

    # Filter for real questions (usually start with "What", "How", etc.)
    filtered_data = [item for item in all_data if len(item['question']) > 10 and len(item['answer']) > 20]
    
    # Randomly sample
    random.seed(seed)
    if len(filtered_data) < count:
        logger.warning(f"Only {len(filtered_data)} questions available after filtering. Using all.")
        sample_batch = filtered_data
    else:
        sample_batch = random.sample(filtered_data, count)

    # 3. Execute Queries and Collect Results
    logger.info(f"Starting evaluation of {len(sample_batch)} test cases...")
    eval_start_time = time.time()
    
    evaluation_results = []
    output_dir = "eval_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Progress file to resume if needed
    progress_file = os.path.join(output_dir, "batch_progress_latest.json")

    for i, item in enumerate(sample_batch, 1):
        question = item['question']
        reference = item['answer']
        
        logger.info(f"[{i}/{len(sample_batch)}] Query: {question[:70]}...")
        
        try:
            # Run the pipeline
            query_obj = MedicalQuery(question=question, mode=UserMode.AUTO)
            processed_query = preprocessor.process_query(query_obj)
            
            gen_start = time.time()
            # We use PATIENT mode for more detailed answers to compare with MedQuAD
            generated_answer = react_agent.run(processed_query, mode=UserMode.PATIENT)
            gen_duration = time.time() - gen_start
            
            # Calculate metrics
            metrics = evaluator.evaluate_single(
                question=question,
                generated_answer=generated_answer.answer,
                reference_answer=reference,
                evidence_texts=generated_answer.evidence_texts or []
            )
            
            # Add metadata
            metrics['confidence'] = generated_answer.confidence
            metrics['generation_time'] = gen_duration
            metrics['num_evidences'] = len(generated_answer.evidence_texts) if generated_answer.evidence_texts else 0
            
            evaluation_results.append(metrics)
            
            # Save periodic progress
            if i % 5 == 0:
                with open(progress_file, "w") as f:
                    json.dump(evaluation_results, f, indent=2)
                logger.info(f"   Progress saved ({i}/{len(sample_batch)})")

        except Exception as e:
            logger.error(f"   ✗ Error on question {i}: {e}")

    # 4. Final Aggregation
    if not evaluation_results:
        logger.error("No questions were successfully evaluated.")
        return

    summary = evaluator.evaluate_batch(evaluation_results)
    summary['total_eval_time'] = time.time() - eval_start_time
    summary['avg_generation_time'] = sum(r['generation_time'] for r in evaluation_results) / len(evaluation_results)
    
    evaluator.print_summary(summary)
    
    # 5. Save Final Report
    report_path = os.path.join(output_dir, f"batch_report_{count}_{int(time.time())}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Batch evaluation complete ({len(evaluation_results)}/{len(sample_batch)})")
    print(f"📄 Report saved to: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch evaluation on Medical RAG QA system")
    parser.add_argument("--count", type=int, default=100, help="Number of questions to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    args = parser.parse_args()
    
    run_batch_evaluation(count=args.count, seed=args.seed)
