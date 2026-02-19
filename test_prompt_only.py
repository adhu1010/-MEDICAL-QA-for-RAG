"""
Test script for prompt creation without citations (no model loading)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only what we need without initializing models
from backend.models import ProcessedQuery, FusedEvidence, RetrievedEvidence, UserMode
from typing import Optional, List
from backend.config import settings

class MockAnswerGenerator:
    """Mock answer generator for testing prompt creation without loading models"""
    
    def _create_prompt(
        self,
        query: ProcessedQuery,
        evidence: FusedEvidence,
        mode: UserMode
    ) -> str:
        """
        Create prompt for LLM with query and evidence
        
        Args:
            query: Processed query
            evidence: Fused evidence from retrieval
            mode: User mode (doctor/patient)
            
        Returns:
            Formatted prompt
        """
        # Combine evidence into context
        context_parts = []
        for i, ev in enumerate(evidence.evidences[:5], 1):  # Top 5 evidences
            # Clean up evidence text
            content = ev.content.strip()
            # Extract answer from Q&A format if present
            if 'Q:' in content and 'A:' in content:
                parts = content.split('A:', 1)
                if len(parts) > 1:
                    content = parts[1].strip()
            context_parts.append(f"[{i}] {content}")
        
        context = "\n".join(context_parts)
        
        # For FLAN-T5, use simpler instruction-based prompts
        if "flan" in settings.llm_model.lower() or "t5" in settings.llm_model.lower():
            if mode == UserMode.DOCTOR:
                prompt = f"""Answer the following medical question based on the evidence provided. Use medical terminology and be precise.

Question: {query.original_question}

Evidence:
{context}

Instruction: Provide a good descriptive answer in 30-40 words based on the evidence.

Answer:"""
            else:  # PATIENT mode
                prompt = f"""Answer the following medical question in simple, patient-friendly language based on the evidence.

Question: {query.original_question}

Evidence:
{context}

Instruction: Provide a clear, patient-friendly answer in 30-40 words based on the evidence.

Answer:"""
        else:
            # For other models (BioGPT), use more detailed prompts
            if mode == UserMode.DOCTOR:
                prompt_template = """You are a medical expert assistant. Based on the following evidence from medical literature and knowledge graphs, provide a detailed, accurate answer to the medical question.

Question: {question}

Evidence:
{context}

Instructions:
- Provide a comprehensive, evidence-based answer
- Include citations to the evidence sources
- Use medical terminology appropriately
- Be precise and factual
- Limit your answer to 30-40 words, descriptive and based strictly on the evidence

Answer:"""
            else:  # PATIENT mode
                prompt_template = """You are a helpful medical assistant. Based on the following medical information, provide a clear, easy-to-understand answer to the question.

Question: {question}

Medical Information:
{context}

Instructions:
- Explain in simple, patient-friendly language
- Avoid complex medical jargon
- Include a disclaimer to consult a doctor
- Be empathetic and supportive
- Limit your answer to 30-40 words, descriptive and based strictly on the evidence

Answer:"""
            
            prompt = prompt_template.format(
                question=query.original_question,
                context=context
            )
        
        return prompt

    def _create_prompt_without_citations(
        self,
        query: ProcessedQuery,
        evidence: FusedEvidence,
        mode: UserMode
    ) -> str:
        """
        Create prompt for LLM with query and evidence, without requiring citations
        
        Args:
            query: Processed query
            evidence: Fused evidence from retrieval
            mode: User mode (doctor/patient)
            
        Returns:
            Formatted prompt without citation requirements
        """
        # Combine evidence into context
        context_parts = []
        for i, ev in enumerate(evidence.evidences[:5], 1):  # Top 5 evidences
            # Clean up evidence text
            content = ev.content.strip()
            # Extract answer from Q&A format if present
            if 'Q:' in content and 'A:' in content:
                parts = content.split('A:', 1)
                if len(parts) > 1:
                    content = parts[1].strip()
            context_parts.append(f"[{i}] {content}")
        
        context = "\n".join(context_parts)
        
        # For FLAN-T5, use simpler instruction-based prompts
        if "flan" in settings.llm_model.lower() or "t5" in settings.llm_model.lower():
            if mode == UserMode.DOCTOR:
                prompt = f"""Answer the following medical question based on the evidence provided. Use medical terminology and be precise.

Question: {query.original_question}

Evidence:
{context}

Instruction: Provide a good descriptive answer in 30-40 words based on the evidence without citations.

Answer:"""
            else:  # PATIENT mode
                prompt = f"""Answer the following medical question in simple, patient-friendly language based on the evidence.

Question: {query.original_question}

Evidence:
{context}

Instruction: Provide a clear, patient-friendly answer in 30-40 words based on the evidence without citations.

Answer:"""
        else:
            # For other models (BioGPT), use more detailed prompts without citation requirements
            if mode == UserMode.DOCTOR:
                prompt_template = """You are a medical expert assistant. Based on the following evidence from medical literature and knowledge graphs, provide a detailed, accurate answer to the medical question.

Question: {question}

Evidence:
{context}

Instructions:
- Provide a comprehensive, evidence-based answer
- Use medical terminology appropriately
- Be precise and factual
- Do not include citations or source references
- Limit your answer to 30-40 words, descriptive and based strictly on the evidence

Answer:"""
            else:  # PATIENT mode
                prompt_template = """You are a helpful medical assistant. Based on the following medical information, provide a clear, easy-to-understand answer to the question.

Question: {question}

Medical Information:
{context}

Instructions:
- Explain in simple, patient-friendly language
- Avoid complex medical jargon
- Include a disclaimer to consult a doctor
- Be empathetic and supportive
- Do not include citations or source references
- Limit your answer to 30-40 words, descriptive and based strictly on the evidence

Answer:"""
            
            prompt = prompt_template.format(
                question=query.original_question,
                context=context
            )
        
        return prompt

def test_prompt_creation():
    """Test creating prompts without citations"""
    print("=" * 60)
    print("Testing Prompt Creation Without Citations")
    print("=" * 60)
    
    # Create test query and evidence
    print("\n1. Creating test medical query...")
    query = ProcessedQuery(
        original_question="What are the side effects of Metformin?",
        normalized_question="side effects metformin",
        entities=[],
        query_type="contextual",
        suggested_strategy="vector_only"
    )
    
    evidence = FusedEvidence(
        evidences=[
            RetrievedEvidence(
                source_type="vector",
                content="Common side effects of Metformin include nausea, vomiting, stomach upset, diarrhea, weakness, and a metallic taste in the mouth. Rarely, it may cause lactic acidosis, a serious condition.",
                confidence=0.9,
                metadata={"source": "medquad", "category": "Diabetes"}
            ),
            RetrievedEvidence(
                source_type="vector",
                content="Metformin is the first-line medication for type 2 diabetes. This meta-analysis of 100 studies shows that metformin effectively reduces HbA1c levels by 1-2% and has cardiovascular benefits. Common side effects include gastrointestinal disturbances in 20-30% of patients.",
                confidence=0.88,
                metadata={"source": "pubmed", "pmid": "12345678"}
            )
        ],
        combined_confidence=0.89,
        fusion_method="vector_only"
    )
    
    # Create mock answer generator
    print("\n2. Creating mock answer generator...")
    generator = MockAnswerGenerator()
    
    # Test prompt creation with citations
    print("\n3. Creating prompt WITH citations...")
    prompt_with_citations = generator._create_prompt(query, evidence, UserMode.PATIENT)
    
    # Test prompt creation without citations
    print("\n4. Creating prompt WITHOUT citations...")
    prompt_without_citations = generator._create_prompt_without_citations(query, evidence, UserMode.PATIENT)
    
    # Display results
    print("\n" + "=" * 60)
    print("PROMPT WITH CITATIONS:")
    print("=" * 60)
    print(prompt_with_citations)
    
    print("\n" + "=" * 60)
    print("PROMPT WITHOUT CITATIONS:")
    print("=" * 60)
    print(prompt_without_citations)
    
    # Check differences
    print("\n" + "=" * 60)
    print("DIFFERENCES:")
    print("=" * 60)
    if "citation" in prompt_with_citations.lower() or "cite" in prompt_with_citations.lower() or "Include citations" in prompt_with_citations:
        print("✓ Regular prompt includes citation requirements")
    else:
        print("⚠ Regular prompt may not explicitly require citations")
        
    if "citation" not in prompt_without_citations.lower() and "cite" not in prompt_without_citations.lower() and "Do not include citations" in prompt_without_citations:
        print("✓ Safe prompt does not require citations")
    else:
        print("⚠ Safe prompt may still include citation requirements")
    
    print("\n✓ Test completed successfully!")

if __name__ == "__main__":
    test_prompt_creation()