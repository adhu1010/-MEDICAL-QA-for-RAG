"""
Evaluation module for measuring system performance
"""
from typing import List, Dict, Any
import json
from pathlib import Path
from loguru import logger
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import numpy as np


class MedicalQAEvaluator:
    """Evaluates medical QA system performance"""
    
    def __init__(self):
        """Initialize evaluator"""
        self.rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        self.smoothing = SmoothingFunction().method1
        logger.info("Evaluator initialized")
    
    def calculate_bleu(self, reference: str, candidate: str) -> float:
        """
        Calculate BLEU score
        
        Args:
            reference: Ground truth answer
            candidate: Generated answer
            
        Returns:
            BLEU score (0-1)
        """
        reference_tokens = reference.lower().split()
        candidate_tokens = candidate.lower().split()
        
        score = sentence_bleu(
            [reference_tokens],
            candidate_tokens,
            smoothing_function=self.smoothing
        )
        
        return score
    
    def calculate_rouge(self, reference: str, candidate: str) -> Dict[str, float]:
        """
        Calculate ROUGE scores
        
        Args:
            reference: Ground truth answer
            candidate: Generated answer
            
        Returns:
            Dict with ROUGE-1, ROUGE-2, ROUGE-L scores
        """
        scores = self.rouge.score(reference, candidate)
        
        return {
            'rouge1': scores['rouge1'].fmeasure,
            'rouge2': scores['rouge2'].fmeasure,
            'rougeL': scores['rougeL'].fmeasure
        }
    
    def calculate_faithfulness(
        self,
        answer: str,
        evidence_texts: List[str]
    ) -> float:
        """
        Calculate faithfulness score (how well answer aligns with evidence)
        
        Args:
            answer: Generated answer
            evidence_texts: Source evidence texts
            
        Returns:
            Faithfulness score (0-1)
        """
        if not evidence_texts:
            return 0.0
        
        # Simple approach: calculate overlap between answer and evidence
        answer_words = set(answer.lower().split())
        
        evidence_words = set()
        for evidence in evidence_texts:
            evidence_words.update(evidence.lower().split())
        
        # Calculate Jaccard similarity
        if not answer_words:
            return 0.0
        
        intersection = answer_words.intersection(evidence_words)
        union = answer_words.union(evidence_words)
        
        faithfulness = len(intersection) / len(union) if union else 0.0
        
        return faithfulness
    
    def detect_hallucination(
        self,
        answer: str,
        evidence_texts: List[str]
    ) -> Dict[str, Any]:
        """
        Detect potential hallucinations in answer
        
        Args:
            answer: Generated answer
            evidence_texts: Source evidence texts
            
        Returns:
            Dict with hallucination detection results
        """
        # Extract medical terms from answer (simple heuristic)
        import re
        medical_terms = re.findall(r'\b[A-Z][a-z]+(?:in|ate|ide|one|ine|cin)\b', answer)
        
        # Check if terms appear in evidence
        evidence_combined = " ".join(evidence_texts)
        
        unsupported_terms = []
        for term in medical_terms:
            if term.lower() not in evidence_combined.lower():
                unsupported_terms.append(term)
        
        hallucination_rate = len(unsupported_terms) / len(medical_terms) if medical_terms else 0.0
        
        return {
            'hallucination_rate': hallucination_rate,
            'unsupported_terms': unsupported_terms,
            'total_medical_terms': len(medical_terms)
        }
    
    def evaluate_single(
        self,
        question: str,
        generated_answer: str,
        reference_answer: str,
        evidence_texts: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate a single QA pair
        
        Args:
            question: The question
            generated_answer: System-generated answer
            reference_answer: Ground truth answer
            evidence_texts: Evidence used for generation
            
        Returns:
            Evaluation metrics
        """
        # Calculate metrics
        bleu = self.calculate_bleu(reference_answer, generated_answer)
        rouge = self.calculate_rouge(reference_answer, generated_answer)
        faithfulness = self.calculate_faithfulness(generated_answer, evidence_texts)
        hallucination = self.detect_hallucination(generated_answer, evidence_texts)
        
        return {
            'question': question,
            'bleu': bleu,
            'rouge': rouge,
            'faithfulness': faithfulness,
            'hallucination': hallucination,
            'answer_length': len(generated_answer.split())
        }
    
    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple test cases
        
        Args:
            test_cases: List of test cases with questions, answers, evidence
            
        Returns:
            Aggregated evaluation results
        """
        results = []
        
        for case in test_cases:
            result = self.evaluate_single(
                question=case['question'],
                generated_answer=case['generated_answer'],
                reference_answer=case['reference_answer'],
                evidence_texts=case.get('evidence_texts', [])
            )
            results.append(result)
        
        # Aggregate metrics
        bleu_scores = [r['bleu'] for r in results]
        rouge1_scores = [r['rouge']['rouge1'] for r in results]
        rouge2_scores = [r['rouge']['rouge2'] for r in results]
        rougeL_scores = [r['rouge']['rougeL'] for r in results]
        faithfulness_scores = [r['faithfulness'] for r in results]
        hallucination_rates = [r['hallucination']['hallucination_rate'] for r in results]
        
        aggregated = {
            'num_cases': len(results),
            'avg_bleu': np.mean(bleu_scores),
            'avg_rouge1': np.mean(rouge1_scores),
            'avg_rouge2': np.mean(rouge2_scores),
            'avg_rougeL': np.mean(rougeL_scores),
            'avg_faithfulness': np.mean(faithfulness_scores),
            'avg_hallucination_rate': np.mean(hallucination_rates),
            'individual_results': results
        }
        
        return aggregated
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save evaluation results to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print evaluation summary"""
        logger.info("\n" + "="*60)
        logger.info("EVALUATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Number of test cases: {results['num_cases']}")
        logger.info(f"Average BLEU:         {results['avg_bleu']:.4f}")
        logger.info(f"Average ROUGE-1:      {results['avg_rouge1']:.4f}")
        logger.info(f"Average ROUGE-2:      {results['avg_rouge2']:.4f}")
        logger.info(f"Average ROUGE-L:      {results['avg_rougeL']:.4f}")
        logger.info(f"Average Faithfulness: {results['avg_faithfulness']:.4f}")
        logger.info(f"Avg Hallucination:    {results['avg_hallucination_rate']:.4f}")
        logger.info("="*60)


def create_sample_test_cases() -> List[Dict[str, Any]]:
    """Create sample test cases for evaluation"""
    return [
        {
            'question': 'What are the side effects of Metformin?',
            'reference_answer': 'Common side effects of Metformin include nausea, diarrhea, and stomach upset.',
            'generated_answer': 'Metformin commonly causes gastrointestinal side effects including nausea, diarrhea, and abdominal discomfort.',
            'evidence_texts': [
                'Metformin side effects include nausea and diarrhea',
                'Common adverse effects are gastrointestinal disturbances'
            ]
        },
        {
            'question': 'What is Type 2 Diabetes?',
            'reference_answer': 'Type 2 diabetes is a metabolic disorder characterized by high blood sugar and insulin resistance.',
            'generated_answer': 'Type 2 diabetes is a chronic condition with elevated blood glucose levels due to insulin resistance.',
            'evidence_texts': [
                'Type 2 diabetes involves insulin resistance',
                'Characterized by hyperglycemia'
            ]
        }
    ]


# Singleton instance
_evaluator_instance = None


def get_evaluator() -> MedicalQAEvaluator:
    """Get or create evaluator singleton"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = MedicalQAEvaluator()
    return _evaluator_instance
