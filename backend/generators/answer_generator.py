"""
Answer generation using LLMs (BioGPT, FLAN-T5, or OpenAI)
"""
from typing import Optional, List
from loguru import logger

from backend.models import (
    FusedEvidence, GeneratedAnswer, ProcessedQuery,
    UserMode
)
from backend.config import settings


class AnswerGenerator:
    """
    Generates medical answers using LLMs with retrieved evidence
    """
    
    def __init__(self, model_type: str = "huggingface"):
        """
        Initialize answer generator
        
        Args:
            model_type: "huggingface" for BioGPT/FLAN-T5 or "openai" for GPT
        """
        self.model_type = model_type
        self.model = None
        self.tokenizer = None
        
        if model_type == "huggingface":
            self._init_huggingface()
        elif model_type == "openai":
            self._init_openai()
    
    def _init_huggingface(self):
        """Initialize HuggingFace model (BioGPT or FLAN-T5)"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
            
            logger.info(f"Loading HuggingFace model: {settings.llm_model}")
            
            # Determine if it's a causal LM (BioGPT) or seq2seq (FLAN-T5)
            if "biogpt" in settings.llm_model.lower():
                self.tokenizer = AutoTokenizer.from_pretrained(settings.llm_model)
                self.model = AutoModelForCausalLM.from_pretrained(settings.llm_model)
            else:
                # Default to seq2seq for FLAN-T5
                self.tokenizer = AutoTokenizer.from_pretrained(settings.llm_model)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(settings.llm_model)
            
            logger.info("HuggingFace model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load HuggingFace model: {e}")
            logger.info("Will use template-based generation as fallback")
            self.model = None
    
    def _init_openai(self):
        """Initialize OpenAI API client"""
        try:
            import openai
            
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            openai.api_key = settings.openai_api_key
            self.model = openai
            logger.info("OpenAI client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.model = None
    
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

Answer:"""
            else:  # PATIENT mode
                prompt = f"""Answer the following medical question in simple, patient-friendly language based on the evidence.

Question: {query.original_question}

Evidence:
{context}

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

Answer:"""
            
            prompt = prompt_template.format(
                question=query.original_question,
                context=context
            )
        
        return prompt
    
    def _generate_with_huggingface(self, prompt: str, evidence_texts: list = None) -> str:
        """Generate answer using HuggingFace model"""
        if not self.model or not self.tokenizer:
            return self._generate_fallback(prompt, evidence_texts)
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            # Check if it's a seq2seq model (FLAN-T5) or causal LM (BioGPT)
            if "flan" in settings.llm_model.lower() or "t5" in settings.llm_model.lower():
                # For seq2seq models, use generate directly
                outputs = self.model.generate(
                    **inputs,
                    max_length=settings.llm_max_tokens,
                    temperature=settings.llm_temperature,
                    do_sample=True,
                    top_p=0.9
                )
            else:
                # For causal LM models
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=settings.llm_max_tokens,
                    temperature=settings.llm_temperature,
                    do_sample=True,
                    top_p=0.9
                )
            
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # For causal models, remove the prompt from the answer
            if "biogpt" in settings.llm_model.lower() and prompt in answer:
                answer = answer.replace(prompt, "").strip()
            
            return answer if answer.strip() else self._generate_fallback(prompt, evidence_texts)
            
        except Exception as e:
            logger.error(f"Error generating with HuggingFace: {e}")
            return self._generate_fallback(prompt, evidence_texts)
    
    def _generate_with_openai(self, prompt: str, evidence_texts: list = None) -> str:
        """Generate answer using OpenAI API"""
        if not self.model:
            return self._generate_fallback(prompt, evidence_texts)
        
        try:
            response = self.model.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable medical assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            
            answer = response.choices[0].message.content
            return answer
            
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            return self._generate_fallback(prompt, evidence_texts)
    
    def _generate_fallback(self, prompt: str, evidence_texts: list = None) -> str:
        """Fallback template-based generation using evidence"""
        logger.info("Using fallback template-based generation")
        
        # If we have evidence, extract and format it
        if evidence_texts and len(evidence_texts) > 0:
            # Combine evidence into a coherent answer
            answer_parts = []
            
            for i, evidence in enumerate(evidence_texts[:3], 1):
                # Clean up the evidence text
                text = evidence.strip()
                
                # Extract answer from Q&A format if present
                if 'Q:' in text and 'A:' in text:
                    # Extract just the answer part
                    parts = text.split('A:', 1)
                    if len(parts) > 1:
                        text = parts[1].strip()
                
                # Add to answer
                answer_parts.append(text)
            
            # Combine all evidence
            combined_answer = ' '.join(answer_parts)
            
            # Remove duplicate sentences (simple deduplication)
            sentences = combined_answer.split('. ')
            unique_sentences = []
            seen = set()
            for sentence in sentences:
                sentence_lower = sentence.lower().strip()
                if sentence_lower and sentence_lower not in seen:
                    unique_sentences.append(sentence)
                    seen.add(sentence_lower)
            
            answer = '. '.join(unique_sentences)
            if not answer.endswith('.'):
                answer += '.'
            
            return answer
        else:
            # No evidence available
            return """I apologize, but I don't have enough medical evidence in my knowledge base to answer this question accurately. Please consult with a qualified healthcare professional for accurate medical information."""
    
    def generate(
        self,
        query: ProcessedQuery,
        evidence: FusedEvidence,
        mode: UserMode = UserMode.PATIENT
    ) -> GeneratedAnswer:
        """
        Generate medical answer from query and evidence
        
        Args:
            query: Processed query
            evidence: Fused evidence
            mode: User mode
            
        Returns:
            GeneratedAnswer with answer text and metadata
        """
        logger.info(f"Generating answer in {mode} mode")
        
        # Create prompt
        prompt = self._create_prompt(query, evidence, mode)
        
        # Extract evidence texts for fallback
        evidence_texts = [ev.content for ev in evidence.evidences]
        
        # Generate answer
        if self.model_type == "huggingface":
            answer_text = self._generate_with_huggingface(prompt, evidence_texts)
        elif self.model_type == "openai":
            answer_text = self._generate_with_openai(prompt, evidence_texts)
        else:
            answer_text = self._generate_fallback(prompt, evidence_texts)
        
        # Add safety disclaimer for patient mode
        if mode == UserMode.PATIENT:
            answer_text += "\n\n⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions."
        
        # Extract sources
        sources = []
        for ev in evidence.evidences[:5]:  # Show up to 5 sources
            source_info = f"{ev.metadata.get('source', 'Unknown').upper()}"
            if 'pmid' in ev.metadata:
                source_info += f" (PMID: {ev.metadata['pmid']})"
            elif 'category' in ev.metadata:
                source_info += f" - {ev.metadata['category']}"
            sources.append(source_info)
        
        generated = GeneratedAnswer(
            answer=answer_text,
            confidence=evidence.combined_confidence,
            sources=sources,
            reasoning=f"Used {len(evidence.evidences)} evidence sources with {evidence.fusion_method}"
        )
        
        logger.info(f"Generated answer with confidence {generated.confidence:.2f}")
        
        return generated


# Singleton instance
_generator_instance = None


def get_answer_generator(model_type: str = "huggingface") -> AnswerGenerator:
    """Get or create AnswerGenerator singleton"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = AnswerGenerator(model_type=model_type)
    return _generator_instance
