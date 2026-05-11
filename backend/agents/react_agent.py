from typing import List, Optional, Any, Dict
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from loguru import logger
import threading

from backend.config import settings, agent_config
from backend.models import ProcessedQuery, MedicalQuery, UserMode, GeneratedAnswer, RetrievalStrategy
from backend.agents.agent_controller import get_agent_controller
from backend.generators.answer_generator import AnswerGenerator
from backend.preprocessing import get_query_preprocessor
from backend.models import UserMode

class MedicalReActAgent:
    """
    ReAct Agent for Medical QA using Meditron (Ollama) with BioGPT fallback.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MedicalReActAgent, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.agent_controller = get_agent_controller()
        self.preprocessor = get_query_preprocessor()
        
        # Initialize fallback generator explicitly as HuggingFace (BioGPT)
        # This ensures we have a dedicated fallback even if main config is Ollama
        self.fallback_generator = AnswerGenerator(model_type="huggingface")
        
        self.enabled = False
        self.agent_executor = None
        
        self._init_agent()
        self._initialized = True

    def _init_agent(self):
        """Initialize the LangChain ReAct Agent"""
        try:
            # Check availability of Ollama
            logger.info(f"Initializing ReAct Agent with model: {settings.ollama_model}")
            
            self.llm = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=0.1,
                keep_alive="5m",
                stop=["\nObservation:", "Observation:"] # Force stop to prevent hallucinating results
            )
            
            # Define Tools
            self.tools = [
                Tool(
                    name="search_medical_knowledge",
                    func=self._search_medical_knowledge,
                    description="Useful for searching medical information. Input should be a simple medical question like 'symptoms of diabetes' or 'aspirin dosage'."
                )
            ]
            
            # Simplified ReAct Prompt for Meditron
            template = '''You are a helpful medical assistant. Answer the user's question using the tools provided.

TOOLS:
------
You have access to the following tools:

{tools}

FORMAT:
-------
To use a tool, please use the following format:

Question: the input question you must answer
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

Begin!

Question: {input}
Thought:{agent_scratchpad}'''

            prompt = PromptTemplate.from_template(template)
            
            # Create Agent
            agent = create_react_agent(self.llm, self.tools, prompt)
            
            # Create Executor
            self.agent_executor = AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                verbose=True, 
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate",
                return_intermediate_steps=True
            )
            
            self.enabled = True
            logger.info("✓ ReAct Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ReAct Agent: {e}")
            logger.warning("Agent execution will default to fallback mechanism")
            self.enabled = False

    def _search_medical_knowledge(self, query_str: str) -> str:
        """
        Tool function to search using AgentController.
        Returns a string representation of the retrieved evidence.
        """
        try:
            logger.info(f"ReAct Tool executing search for: {query_str}")
            
            # Create a MedicalQuery object
            # We assume AUTO mode for tool-based queries to let the system decide
            med_query = MedicalQuery(question=query_str, mode=UserMode.AUTO)
            
            # Process query to get entities and strategy
            processed = self.preprocessor.process_query(med_query)
            
            # Execute retrieval via AgentController
            fused = self.agent_controller.execute(processed)
            
            # Store the fused evidence for source extraction later
            self._last_fused_evidence = fused
            
            if not fused.evidences:
                return "No relevant medical information found."
            
            # Format output for the agent with proper source labels
            results = []
            for i, ev in enumerate(fused.evidences[:5], 1): # Top 5 evidences
                content = ev.content.strip()
                # Truncate very long content to fit context window
                if len(content) > 500:
                    content = content[:500] + "..."
                
                # Build rich source label
                source_name = ev.metadata.get('source', ev.source_type).lower()
                if source_name == 'medquad':
                    source_label = f"MedQuAD - {ev.metadata.get('category', 'General')}"
                elif source_name == 'pubmed':
                    pmid = ev.metadata.get('pmid', '')
                    source_label = f"PubMed (PMID: {pmid})" if pmid else "PubMed"
                elif source_name == 'knowledge_graph':
                    source_label = f"Knowledge Graph - {ev.metadata.get('category', ev.metadata.get('predicate', ''))}"
                else:
                    source_label = f"{ev.source_type.upper()} Retriever"
                
                results.append(f"[{i}] {content} (Source: {source_label})")
            
            return "\n\n".join(results)
            
        except Exception as e:
            logger.error(f"Error in search tool: {e}")
            return f"Error occurred during search: {str(e)}"

    def run(self, query: ProcessedQuery, mode: UserMode = UserMode.AUTO) -> GeneratedAnswer:
        """
        Run the ReAct agent with fallback to BioGPT.
        """
        if not self.enabled:
            logger.warning("ReAct Agent disabled, using fallback.")
            return self._fallback(query, mode)
            
        try:
            logger.info(f"Running ReAct Agent for query: {query.original_question}")
            
            # Add specific instructions based on Mode
            instruction = ""
            if mode == UserMode.PATIENT:
                instruction = " Answer in simple, patient-friendly language. Explain medical terms."
            else:
                instruction = " Answer with professional medical terminology. Be concise."
            
            input_text = f"{query.original_question}{instruction}"
            
            # Invoke Agent
            response = self.agent_executor.invoke({"input": input_text})
            final_answer_text = response.get("output", "")
            intermediate_steps = response.get("intermediate_steps", [])
            
            # Extract evidence from tool observations
            evidence_texts = []
            for action, observation in intermediate_steps:
                if action.tool == "search_medical_knowledge":
                    evidence_texts.append(str(observation))
            
            # Extract source labels from the last fused evidence
            sources = []
            seen_sources = set()
            fused = getattr(self, '_last_fused_evidence', None)
            if fused and fused.evidences:
                for ev in fused.evidences[:5]:
                    source_name = ev.metadata.get('source', '').lower()
                    if source_name == 'medquad':
                        category = ev.metadata.get('category', 'General')
                        focus = ev.metadata.get('focus', '')
                        label = f"MedQuAD - {category}"
                        if focus:
                            label += f" ({focus})"
                    elif source_name == 'pubmed':
                        pmid = ev.metadata.get('pmid', '')
                        label = f"PubMed (PMID: {pmid})" if pmid else "PubMed"
                    elif source_name == 'knowledge_graph':
                        category = ev.metadata.get('category', '')
                        label = f"Knowledge Graph - {category}" if category else "Knowledge Graph"
                    elif source_name == 'bm25_index':
                        category = ev.metadata.get('category', '')
                        label = f"BM25 Index - {category}" if category else "BM25 Sparse Index"
                    else:
                        label = f"{ev.source_type.upper()} Retriever"
                    if label not in seen_sources:
                        sources.append(label)
                        seen_sources.add(label)
            
            # Validate Answer
            if not final_answer_text or "Agent stopped" in final_answer_text:
                raise ValueError("Agent produced empty or invalid answer")
                
            return GeneratedAnswer(
                answer=final_answer_text,
                confidence=0.85, # ReAct generally yields higher confidence if successful
                sources=sources,
                reasoning="Generated via Meditron ReAct Agent",
                evidence_texts=evidence_texts,
                metadata={'agent_type': 'react_meditron', 'intermediate_steps_count': len(intermediate_steps)}
            )
            
        except Exception as e:
            logger.error(f"ReAct Agent run failed: {e}")
            return self._fallback(query, mode)

    def _fallback(self, query: ProcessedQuery, mode: UserMode) -> GeneratedAnswer:
        """Fallback to BioGPT / Standard RAG Pipeline"""
        logger.info("⚠️ Initiating Fallback to BioGPT/Standard Pipeline")
        
        try:
            # 1. Retrieve Evidence (Standard Way)
            fused_evidence = self.agent_controller.execute(query)
            
            # 2. Add metadata about fallback
            if not hasattr(fused_evidence, 'metadata'):
                fused_evidence.metadata = {}
            fused_evidence.metadata['fallback_to_biogpt'] = True
            
            # 3. Generate Answer using the fallback generator (BioGPT)
            generated = self.fallback_generator.generate(query, fused_evidence, mode)
            
            # 4. Attach evidence texts for safety check and metadata
            generated.evidence_texts = [ev.content for ev in fused_evidence.evidences]
            generated.metadata.update(fused_evidence.metadata)
            generated.metadata['agent_type'] = 'fallback_rag_biogpt'
            
            return generated
            
        except Exception as e:
            logger.error(f"Critical Fallback Failure: {e}")
            # Ultimate safety net
            return GeneratedAnswer(
                answer="I apologize, but I am currently unable to provide an answer due to a system error. Please consult a healthcare professional.",
                confidence=0.0,
                sources=[],
                reasoning="System Error",
                evidence_texts=[],
                metadata={'error': str(e)}
            )

def get_react_agent() -> MedicalReActAgent:
    """Get singleton instance of ReAct Agent"""
    return MedicalReActAgent()
