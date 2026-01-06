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
            
            self.model = openai.OpenAI(api_key=settings.openai_api_key)
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
    
    def _generate_with_openai(self, prompt: str, evidence_texts: Optional[List[str]] = None) -> str:
        """Generate answer using OpenAI API"""
        if not self.model:
            return self._generate_fallback(prompt, evidence_texts or [])
        
        try:
            # Type ignore for OpenAI API since it's dynamically typed
            response = self.model.chat.completions.create(  # type: ignore
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable medical assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            
            # Type ignore for OpenAI API since it's dynamically typed
            answer = response.choices[0].message.content  # type: ignore
            return answer or ""
            
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            return self._generate_fallback(prompt, evidence_texts or [])

    def _generate_with_huggingface(self, prompt: str, evidence_texts: Optional[List[str]] = None) -> str:
        """Generate answer using HuggingFace model"""
        if not self.model or not self.tokenizer:
            return self._generate_fallback(prompt, evidence_texts or [])
        
        try:
            # Tokenize inputs
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

            # Build generation kwargs
            gen_kwargs = {
                'temperature': settings.llm_temperature,
                'top_p': 0.9,
            }
            eos_id = getattr(self.tokenizer, 'eos_token_id', None)
            if eos_id is not None:
                gen_kwargs['eos_token_id'] = eos_id

            # Use model-appropriate generation parameters
            if "flan" in settings.llm_model.lower() or "t5" in settings.llm_model.lower():
                # Seq2seq models: use max_length
                gen_kwargs.update({
                    'max_length': settings.llm_max_tokens,
                    'do_sample': True
                })
                outputs = self.model.generate(  # type: ignore
                    **inputs,
                    **gen_kwargs
                )
            else:
                # Causal models: request only new tokens
                gen_kwargs.update({
                    'max_new_tokens': settings.llm_max_tokens,
                    'do_sample': True
                })
                outputs = self.model.generate(  # type: ignore
                    **inputs,
                    **gen_kwargs
                )

            # Decode only the new tokens (avoid echoing prompt)
            try:
                input_ids = inputs.get('input_ids', None)
                input_len = input_ids.shape[1] if input_ids is not None else 0
            except Exception:
                input_len = 0

            generated_ids = outputs[0]
            try:
                if generated_ids.shape[1] > input_len:
                    gen_only = generated_ids[:, input_len:]
                else:
                    gen_only = generated_ids
            except Exception:
                gen_only = generated_ids

            answer = self.tokenizer.decode(gen_only[0], skip_special_tokens=True)

            logger.info(f"BioGPT raw output length: {len(answer)} chars")
            logger.debug(f"BioGPT raw output: {answer[:500]}...")

            # Post-cleaning similar to previous logic: extract after Answer: if present
            if "biogpt" in settings.llm_model.lower() and "Answer:" in answer:
                parts = answer.split("Answer:")
                answer = parts[-1].strip()

            # General cleanup of artifacts
            answer = answer.replace("</s>", "").replace("", "").strip()
            answer = answer.replace("<FREETEXT>", "").replace("</FREETEXT>", "").strip()
            answer = answer.replace("<ABSTRACT>", "").replace("</ABSTRACT>", "").strip()
            answer = answer.replace("▃", "").strip()
            answer = " ".join(answer.split())

            if not answer or len(answer) < 10:
                logger.warning("Answer quality check failed, using fallback generation")
                return self._generate_fallback(prompt, evidence_texts or [])

            return answer

        except Exception as e:
            logger.error(f"Error generating with HuggingFace: {e}")
            return self._generate_fallback(prompt, evidence_texts or [])

    def _generate_fallback(self, prompt: str, evidence_texts: Optional[List[str]] = None) -> str:
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
            
            # Limit to 30-40 words for consistency
            words = answer.split()
            if len(words) > 40:
                answer = " ".join(words[:40]).rstrip(".,;:!?")
                
            return answer
        else:
            # No evidence available
            return "I apologize, but I don't have enough medical evidence in my knowledge base to answer this question accurately. Please consult with a qualified healthcare professional for accurate medical information."

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

    def _generate_without_citations(self, prompt: str, evidence_texts: Optional[List[str]] = None) -> str:
        """Generate answer using HuggingFace model without citations"""
        if not self.model or not self.tokenizer:
            return self._generate_fallback(prompt, evidence_texts or [])
        
        try:
            # Tokenize inputs
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

            # Build generation kwargs
            gen_kwargs = {
                'temperature': settings.llm_temperature,
                'top_p': 0.9,
            }
            eos_id = getattr(self.tokenizer, 'eos_token_id', None)
            if eos_id is not None:
                gen_kwargs['eos_token_id'] = eos_id

            # Use model-appropriate generation parameters
            if "flan" in settings.llm_model.lower() or "t5" in settings.llm_model.lower():
                gen_kwargs.update({
                    'max_length': settings.llm_max_tokens,
                    'do_sample': True
                })
                outputs = self.model.generate(  # type: ignore
                    **inputs,
                    **gen_kwargs
                )
            else:
                gen_kwargs.update({
                    'max_new_tokens': settings.llm_max_tokens,
                    'do_sample': True
                })
                outputs = self.model.generate(  # type: ignore
                    **inputs,
                    **gen_kwargs
                )

            # Decode only the new tokens (avoid echoing prompt)
            try:
                input_ids = inputs.get('input_ids', None)
                input_len = input_ids.shape[1] if input_ids is not None else 0
            except Exception:
                input_len = 0

            generated_ids = outputs[0]
            try:
                if generated_ids.shape[1] > input_len:
                    gen_only = generated_ids[:, input_len:]
                else:
                    gen_only = generated_ids
            except Exception:
                gen_only = generated_ids

            answer = self.tokenizer.decode(gen_only[0], skip_special_tokens=True)

            logger.info(f"BioGPT raw output length: {len(answer)} chars")
            logger.debug(f"BioGPT raw output: {answer[:500]}...")

            if "biogpt" in settings.llm_model.lower() and "Answer:" in answer:
                parts = answer.split("Answer:")
                answer = parts[-1].strip()

            # General cleanup of artifacts
            answer = answer.replace("</s>", "").replace("", "").strip()
            answer = answer.replace("<FREETEXT>", "").replace("</FREETEXT>", "").strip()
            answer = answer.replace("<ABSTRACT>", "").replace("</ABSTRACT>", "").strip()
            answer = answer.replace("▃", "").strip()
            answer = " ".join(answer.split())

            if not answer or len(answer) < 10:
                logger.warning("Answer quality check failed, using fallback generation")
                return self._generate_fallback(prompt, evidence_texts or [])

            return answer

        except Exception as e:
            logger.error(f"Error generating with HuggingFace: {e}")
            return self._generate_fallback(prompt, evidence_texts or [])

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
        
        # Generate answer using BioGPT/selected HuggingFace model with concise 30-40 word summary
        logger.info("Generating answer with HuggingFace model (BioGPT) constrained to 30-40 words")
        answer_text = self._generate_with_huggingface(
            prompt + "\n\nConstraints: Provide a detailed medical answer in 30-40 words.",
            evidence_texts=evidence_texts
        )
        # Enforce 30-40 word limit post-processing
        words = answer_text.split()
        if len(words) > 40:
            answer_text = " ".join(words[:40]).rstrip(".,;:!?")
        
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

    def generate_without_citations(
        self,
        query: ProcessedQuery,
        evidence: FusedEvidence,
        mode: UserMode = UserMode.PATIENT
    ) -> GeneratedAnswer:
        """
        Generate medical answer from query and evidence without citations
        
        This method is used when a safe answer is needed but citations should be removed.
        
        Args:
            query: Processed query
            evidence: Fused evidence
            mode: User mode
            
        Returns:
            GeneratedAnswer with answer text and metadata (without citations)
        """
        logger.info(f"Generating answer without citations in {mode} mode")
        # Extract evidence texts for fallback
        evidence_texts = [ev.content for ev in evidence.evidences]
        
        # Create prompt without citations
        prompt = self._create_prompt_without_citations(query, evidence, mode)

        # Generate answer using HuggingFace model (BioGPT) without citations
        logger.info("Generating answer with HuggingFace model (BioGPT) without citations")
        answer_text = self._generate_without_citations(
            prompt + "\n\nConstraints: Provide a detailed medical answer in 30-40 words without citations.",
            evidence_texts=evidence_texts
        )
        # Enforce 30-40 word limit post-processing
        words = answer_text.split()
        if len(words) > 40:
            answer_text = " ".join(words[:40]).rstrip(".,;:!?")
        
        # Add safety disclaimer for patient mode
        if mode == UserMode.PATIENT:
            answer_text += "\n\n⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions."
        
        # Return answer without source citations
        generated = GeneratedAnswer(
            answer=answer_text,
            confidence=evidence.combined_confidence,
            sources=[],  # No citations in this mode
            reasoning=f"Used {len(evidence.evidences)} evidence sources with {evidence.fusion_method} (citations removed for safety)"
        )
        
        logger.info(f"Generated answer without citations with confidence {generated.confidence:.2f}")
        
        return generated

# Singleton instance
_generator_instance = None


def get_answer_generator(model_type: str = "huggingface") -> AnswerGenerator:
    """Get or create AnswerGenerator singleton"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = AnswerGenerator(model_type=model_type)
    return _generator_instance
