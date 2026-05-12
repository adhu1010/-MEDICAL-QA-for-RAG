"""
Answer generation using LLMs (Ollama/Meditron, BioGPT, FLAN-T5, or OpenAI)
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
            model_type: "ollama" for Meditron, "huggingface" for BioGPT/FLAN-T5, or "openai" for GPT
        """
        # Use backend setting from config if not explicitly specified
        if model_type == "huggingface" and hasattr(settings, 'llm_backend'):
            model_type = settings.llm_backend

        self.model_type = model_type
        self.model = None
        self.tokenizer = None
        self.ollama_client = None

        if model_type == "ollama":
            self._init_ollama()
        elif model_type == "huggingface":
            self._init_huggingface()
        elif model_type == "openai":
            self._init_openai()

    def _init_ollama(self):
        """Initialize Ollama client for Meditron or other local models"""
        try:
            import ollama

            logger.info(
                f"Initializing Ollama client: {settings.ollama_base_url}")
            logger.info(f"Model: {settings.ollama_model}")

            # Test connection to Ollama
            try:
                ollama.list()
                self.ollama_client = ollama
                logger.info("✓ Ollama client initialized successfully")
            except Exception as conn_err:
                logger.error(
                    f"Cannot connect to Ollama at {settings.ollama_base_url}: {conn_err}")
                logger.warning("Falling back to HuggingFace BioGPT")
                self.model_type = "huggingface"
                self._init_huggingface()

        except ImportError as e:
            logger.error(f"Ollama library not installed: {e}")
            logger.warning("Install with: pip install ollama")
            logger.warning("Falling back to HuggingFace BioGPT")
            self.model_type = "huggingface"
            self._init_huggingface()

    def _init_huggingface(self):
        """Initialize HuggingFace model (BioGPT or FLAN-T5)"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM

            logger.info(f"Loading HuggingFace model: {settings.llm_model}")

            # Determine if it's a causal LM (BioGPT) or seq2seq (FLAN-T5)
            if "biogpt" in settings.llm_model.lower():
                self.tokenizer = AutoTokenizer.from_pretrained(
                    settings.llm_model)
                self.model = AutoModelForCausalLM.from_pretrained(
                    settings.llm_model)
            else:
                # Default to seq2seq for FLAN-T5
                self.tokenizer = AutoTokenizer.from_pretrained(
                    settings.llm_model)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    settings.llm_model)

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
        # Filter out very low confidence evidence to prevent hallucination distractions
        valid_evidences = [ev for ev in evidence.evidences if ev.confidence >= 0.4]
        
        for i, ev in enumerate(valid_evidences[:5], 1):  # Top 5 valid evidences
            # Clean up evidence text
            content = ev.content.strip()
            
            # Extract answer from MedQuAD Q&A format
            if 'Answer:' in content:
                content = content.split('Answer:', 1)[-1].strip()
            elif 'A:' in content:
                content = content.split('A:', 1)[-1].strip()
                
            # If there's still a Question: at the start, remove it
            if content.startswith('Question:'):
                content = content.split('\n', 1)[-1].strip()
            
            # Truncate very long evidence entries (increased to 800)
            if len(content) > 800:
                content = content[:800] + "..."
            context_parts.append(f"- {content}")

        context = "\n".join(context_parts)

        # Use Meditron-specific format if using Ollama
        if self.model_type == "ollama":
            return self._create_meditron_prompt(query, context, mode)

        # Otherwise use default format

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
            # For other models (BioGPT), use VERY CONCISE prompts to prevent hallucination
            # BioGPT works best with short, direct prompts that emphasize evidence
            if mode == UserMode.DOCTOR:
                prompt_template = """Based on this medical evidence, answer the question.

Evidence:
{context}

Question: {question}

Provide a 30-40 word medical answer based ONLY on the evidence above.

Answer:"""
            else:  # PATIENT mode
                prompt_template = """Based on this medical information, answer the question in simple language.

Medical Information:
{context}

Question: {question}

Provide a simple 30-40 word answer based ONLY on the information above.

Answer:"""

            prompt = prompt_template.format(
                question=query.original_question,
                context=context
            )

        return prompt

    def _create_meditron_prompt(
        self,
        query: ProcessedQuery,
        context: str,
        mode: UserMode
    ) -> str:
        """
        Create prompt specifically formatted for Meditron model.

        Meditron works best with SHORT, direct prompts for faster CPU inference.

        Args:
            query: Processed query
            context: Pre-formatted evidence context
            mode: User mode (doctor/patient)

        Returns:
            Meditron-optimized prompt (simplified for speed)
        """
        question = query.original_question

        # SIMPLIFIED prompts for faster generation on CPU
        if mode == UserMode.DOCTOR:
            prompt = f"""Medical Context:
{context}

Question: {question}

Provide a detailed, comprehensive medical answer. Answer the question and summarize the condition:"""
        else:  # PATIENT mode
            prompt = f"""Health Info:
{context}

Question: {question}

Provide a detailed, comprehensive answer. First answer the question, then explain what the condition is in simple terms:"""

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
                    {"role": "system",
                        "content": "You are a knowledgeable medical assistant."},
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

    def _generate_with_ollama(self, prompt: str, evidence_texts: Optional[List[str]] = None) -> str:
        """Generate answer using Ollama (Meditron or other local models)"""
        if not self.ollama_client:
            logger.warning("Ollama client not available, using fallback")
            return self._generate_fallback(prompt, evidence_texts or [])

        try:
            logger.info(
                f"Generating with Ollama model: {settings.ollama_model}")

            # Simple, direct prompt for faster inference
            full_prompt = prompt

            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=full_prompt,
                options={
                    'temperature': 0.7,
                    'num_predict': 400,  # Increased to allow full detailed explanations
                    'num_ctx': 2048,     # Limit context window
                    'top_p': 0.9,
                    'top_k': 40,
                    'repeat_penalty': 1.1
                },
                raw=True  # Bypass model template
            )

            answer = response.get('response', '').strip()
            logger.debug(
                f"Raw Ollama response: {answer[:300] if answer else 'empty'}")

            # Clean up common artifacts from Meditron/Llama models
            answer = self._clean_meditron_response(answer)

            if not answer or len(answer) < 20:
                logger.warning(
                    f"Ollama generated short/empty answer: {len(answer) if answer else 0} chars")
                return self._generate_fallback(prompt, evidence_texts or [])

            logger.info(f"Ollama generated {len(answer)} character answer")
            return answer

        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            logger.warning("Falling back to template-based generation")
            return self._generate_fallback(prompt, evidence_texts or [])

    def _clean_meditron_response(self, answer: str) -> str:
        """
        Clean up Meditron/Llama model output.

        Removes common artifacts like:
        - Chat template markers
        - System prompt leakage
        - Prompt echo (when model repeats the prompt)
        - Trailing incomplete sentences
        """
        if not answer:
            return ""

        # First, check if the model echoed the prompt - strip everything before "Detailed Answer:"
        if 'Detailed Answer:' in answer and answer.index('Detailed Answer:') < len(answer) / 2:
            answer = answer.split('Detailed Answer:', 1)[-1].strip()
        elif answer.startswith('Answer:') or ( 'Answer:' in answer and answer.index('Answer:') < 50):
            answer = answer.split('Answer:', 1)[-1].strip()

        # If the model starts hallucinating new questions, chop it off!
        if '\nQuestion:' in answer:
            answer = answer.split('\nQuestion:')[0].strip()
        elif '\nQ:' in answer:
            answer = answer.split('\nQ:')[0].strip()

        # Remove common prompt echoes
        prompt_echoes = [
            'Provide a clear medical answer:',
            'Answer in simple terms:',
            'Provide a helpful medical answer based on the information above:',
            'Provide a detailed, comprehensive medical answer.',
            'Provide a detailed, comprehensive answer.',
            'First answer the question, then explain what the condition is in simple terms:',
            'Answer the question and summarize the condition:',
            'You are a helpful medical',
            'Health Info:',
            'Medical Context:'
        ]
        for echo in prompt_echoes:
            if answer.lower().startswith(echo.lower()):
                answer = answer[len(echo):].strip()
            # Also remove from anywhere in the answer
            answer = answer.replace(echo, '').strip()

        # Remove prompt echo patterns (model repeating the context)
        prompt_echo_patterns = [
            'Health Information:', 'Medical Evidence:', 'Medical Information:',
            'Evidence:', 'Context:'
        ]
        
        # Aggressively remove "Question: [question text]" lines
        lines = answer.split('\n')
        cleaned_lines = []
        skip_mode = True
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
                
            # Skip lines starting with Question:
            if line_stripped.startswith("Question:"):
                # verify it is likely an echo (e.g. Question: What is a stroke?)
                if "?" in line_stripped or len(line_stripped) < 100:
                    continue
            
            # Skip lines that are just "Answer:"
            if line_stripped == "Answer:":
                continue

            # Skip lines that are part of evidence echo
            if skip_mode and any(p in line_stripped for p in prompt_echo_patterns):
                continue
            
            # Once we see real content (not evidence/question), stop skipping
            skip_mode = False
            cleaned_lines.append(line)
                
        answer = ' '.join(cleaned_lines)

        # Remove common model artifacts
        artifacts = [
            "</s>", "<s>", "<|im_end|>", "<|im_start|>",
            "[INST]", "[/INST]", "<<SYS>>", "<</SYS>>",
            "assistant", "Assistant:", "###", "```",
            "# Discussion", "# Conclusions", "# Background", "# Methods",
            "# Results", "# Abstract", "## ", "# "
        ]
        for artifact in artifacts:
            answer = answer.replace(artifact, "")

        # Remove lines that look like system prompts or template leakage
        # ... (rest of cleanup logic) ...
        
        return answer.strip()

    def _generate_with_huggingface(self, prompt: str, evidence_texts: Optional[List[str]] = None) -> str:
        """Generate answer using HuggingFace model (BioGPT) grounded in evidence"""
        if not self.model or not self.tokenizer:
            return self._generate_fallback(prompt, evidence_texts or [])

        try:
            # BioGPT-specific: Use concise, focused prompt to prevent empty generation
            # Truncate long prompts to ensure model can generate
            inputs = self.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=400)

            # Build generation kwargs - CRITICAL for BioGPT
            gen_kwargs = {
                'max_new_tokens': 100,  # Generate 60-100 tokens (~40-70 words)
                'min_new_tokens': 30,   # Force minimum generation
                'do_sample': True,
                'temperature': 0.3,     # LOW temp = less creativity = LESS HALLUCINATION
                'top_p': 0.85,          # More focused sampling
                'top_k': 40,            # Reduced from 50
                'repetition_penalty': 1.3,  # Increased from 1.2 - stronger penalty
                'no_repeat_ngram_size': 3,
            }

            eos_id = getattr(self.tokenizer, 'eos_token_id', None)
            pad_id = getattr(self.tokenizer, 'pad_token_id', None)
            if eos_id is not None:
                gen_kwargs['eos_token_id'] = eos_id
            if pad_id is not None:
                gen_kwargs['pad_token_id'] = pad_id

            # Use model-appropriate generation parameters
            if "flan" in settings.llm_model.lower() or "t5" in settings.llm_model.lower():
                # Seq2seq models: use max_length
                gen_kwargs.update({
                    'max_length': settings.llm_max_tokens,
                })
                outputs = self.model.generate(  # type: ignore
                    **inputs,
                    **gen_kwargs
                )
            else:
                # Causal models like BioGPT: generate new tokens only
                outputs = self.model.generate(  # type: ignore
                    **inputs,
                    **gen_kwargs
                )

            # Decode only the new tokens (avoid echoing prompt)
            input_ids = inputs.get('input_ids', None)
            input_len = input_ids.shape[1] if input_ids is not None else 0

            generated_ids = outputs[0]
            if generated_ids.shape[0] > input_len:
                gen_only = generated_ids[input_len:]
            else:
                gen_only = generated_ids

            answer = self.tokenizer.decode(gen_only, skip_special_tokens=True)

            logger.info(f"BioGPT raw output length: {len(answer)} chars")
            logger.debug(f"BioGPT raw output: {answer[:500]}...")

            # Clean up BioGPT output artifacts
            answer = answer.replace("</s>", "").replace("<pad>", "").strip()
            answer = answer.replace("<FREETEXT>", "").replace(
                "</FREETEXT>", "").strip()
            answer = answer.replace("<ABSTRACT>", "").replace(
                "</ABSTRACT>", "").strip()
            answer = answer.replace("▃", "").strip()

            # Remove any remaining "Answer:" prefixes
            if "Answer:" in answer:
                answer = answer.split("Answer:", 1)[-1].strip()

            # Normalize whitespace
            answer = " ".join(answer.split())

            # CRITICAL: If generation failed, use evidence-based fallback
            if not answer or len(answer) < 10:
                logger.warning(
                    f"BioGPT generated empty/short response ({len(answer)} chars), using evidence-based fallback")
                return self._generate_fallback(prompt, evidence_texts or [])

            logger.info(
                f"BioGPT successfully generated {len(answer)} character answer")
            return answer

        except Exception as e:
            logger.error(f"Error generating with HuggingFace: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
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
            inputs = self.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=512)

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

            answer = self.tokenizer.decode(
                gen_only[0], skip_special_tokens=True)

            logger.info(f"BioGPT raw output length: {len(answer)} chars")
            logger.debug(f"BioGPT raw output: {answer[:500]}...")

            if "biogpt" in settings.llm_model.lower() and "Answer:" in answer:
                parts = answer.split("Answer:")
                answer = parts[-1].strip()

            # General cleanup of artifacts
            answer = answer.replace("</s>", "").replace("", "").strip()
            answer = answer.replace("<FREETEXT>", "").replace(
                "</FREETEXT>", "").strip()
            answer = answer.replace("<ABSTRACT>", "").replace(
                "</ABSTRACT>", "").strip()
            answer = answer.replace("▃", "").strip()
            answer = " ".join(answer.split())

            if not answer or len(answer) < 10:
                logger.warning(
                    "Answer quality check failed, using fallback generation")
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

        # CRITICAL: Enforce minimum confidence threshold to prevent hallucination
        MIN_CONFIDENCE = 0.25  # 25% minimum confidence required
        if evidence.combined_confidence < MIN_CONFIDENCE:
            logger.warning(
                f"Evidence confidence too low ({evidence.combined_confidence:.2f} < {MIN_CONFIDENCE}). "
                "Refusing to generate potentially hallucinated answer."
            )
            return GeneratedAnswer(
                answer="I don't have enough reliable information in my medical knowledge base to answer this question accurately. For accurate medical information about this topic, please consult with a qualified healthcare professional.",
                confidence=0.0,
                sources=[],
                reasoning=f"Insufficient evidence confidence: {evidence.combined_confidence:.2f} < {MIN_CONFIDENCE}"
            )

        # Create prompt
        prompt = self._create_prompt(query, evidence, mode)

        # Extract evidence texts for fallback
        evidence_texts = [ev.content for ev in evidence.evidences]

        # Generate answer based on backend type
        if self.model_type == "ollama":
            logger.info(
                f"Generating answer with Ollama model ({settings.ollama_model}) - detailed mode")
            answer_text = self._generate_with_ollama(
                prompt,
                evidence_texts=evidence_texts
            )
        else:
            # Use HuggingFace (BioGPT) or fallback
            logger.info(
                "Generating answer with HuggingFace model (BioGPT) constrained to 30-40 words")
            answer_text = self._generate_with_huggingface(
                prompt + "\n\nConstraints: Provide a detailed medical answer in 30-40 words.",
                evidence_texts=evidence_texts
            )
            # Enforce 30-40 word limit only for BioGPT (to prevent hallucination)
            words = answer_text.split()
            if len(words) > 40:
                answer_text = " ".join(words[:40]).rstrip(".,;:!?")

        # Add safety disclaimer for patient mode
        if mode == UserMode.PATIENT:
            answer_text += "\n\n⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions."

        # Extract sources
        sources = []
        seen_sources = set()  # Avoid duplicate source labels
        for ev in evidence.evidences[:5]:  # Show up to 5 sources
            source_name = ev.metadata.get('source', '').lower()
            source_label = ""

            if source_name == 'medquad':
                category = ev.metadata.get('category', 'General')
                focus = ev.metadata.get('focus', '')
                source_label = f"MedQuAD - {category}"
                if focus:
                    source_label += f" ({focus})"
            elif source_name == 'pubmed':
                pmid = ev.metadata.get('pmid', '')
                journal = ev.metadata.get('journal', '')
                if pmid:
                    source_label = f"PubMed (PMID: {pmid})"
                elif journal:
                    source_label = f"PubMed - {journal}"
                else:
                    source_label = "PubMed"
            elif source_name == 'knowledge_graph':
                category = ev.metadata.get('category', '')
                predicate = ev.metadata.get('predicate', '')
                if category:
                    source_label = f"Knowledge Graph - {category}"
                elif predicate:
                    source_label = f"Knowledge Graph ({predicate})"
                else:
                    source_label = "Knowledge Graph"
            elif source_name == 'bm25_index':
                # BM25 sparse retrieval - check if original data source info is available
                category = ev.metadata.get('category', '')
                if category:
                    source_label = f"BM25 Index - {category}"
                else:
                    source_label = "BM25 Sparse Index"
            elif source_name == 'vector_db':
                source_label = "Vector Database"
            else:
                # Fallback: use source_type from evidence
                source_label = f"{ev.source_type.upper()} Retriever"

            # Deduplicate sources
            if source_label and source_label not in seen_sources:
                sources.append(source_label)
                seen_sources.add(source_label)

        generated = GeneratedAnswer(
            answer=answer_text,
            confidence=evidence.combined_confidence,
            sources=sources,
            reasoning=f"Used {len(evidence.evidences)} evidence sources with {evidence.fusion_method}"
        )

        logger.info(
            f"Generated answer with confidence {generated.confidence:.2f}")

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
        logger.info(
            "Generating answer with HuggingFace model (BioGPT) without citations")
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

        logger.info(
            f"Generated answer without citations with confidence {generated.confidence:.2f}")

        return generated


# Singleton instance
_generator_instance = None


def get_answer_generator(model_type: str = "huggingface") -> AnswerGenerator:
    """Get or create AnswerGenerator singleton"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = AnswerGenerator(model_type=model_type)
    return _generator_instance
