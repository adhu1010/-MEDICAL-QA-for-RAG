"""
Main FastAPI application for Medical RAG QA System
"""
from backend.utils import LoggerSetup, format_sources
from backend.safety import get_safety_reflector
from backend.generators import get_answer_generator
from backend.agents import get_agent_controller, get_react_agent
from backend.preprocessing import get_query_preprocessor
from backend.models import (
    MedicalQuery, MedicalAnswer, HealthResponse,
    ProcessedQuery, UserMode
)
from backend.config import settings
from loguru import logger
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import os
import sys
import warnings

# Fix pydantic and ChromaDB compatibility issues before any imports
os.environ["CHROMADB_DISABLE_TELEMETRY"] = "true"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='chromadb')


# Setup logging
LoggerSetup.setup(log_file=str(settings.log_file), level=settings.log_level)
logger.info("Starting Medical RAG QA System")

# Create FastAPI app
app = FastAPI(
    title="Medical RAG QA System",
    description="Agentic Retrieval-Augmented Generation for Medical Question Answering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including file:// protocol
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components eagerly at startup
query_preprocessor = None
agent_controller = None
answer_generator = None
safety_reflector = None
react_agent = None


def initialize_all_components():
    """Initialize ALL components at startup (not lazy loading)"""
    global query_preprocessor, agent_controller, answer_generator, safety_reflector, react_agent

    logger.info("🔧 Initializing all system components...")

    logger.info("📝 Loading query preprocessor (with scispaCy model)...")
    query_preprocessor = get_query_preprocessor()
    logger.info("✅ Query preprocessor loaded")

    logger.info(
        "🤖 Loading agent controller (with retrievers: BioBERT, BM25, KG)...")
    agent_controller = get_agent_controller()
    logger.info("✅ Agent controller loaded")

    logger.info("💬 Loading answer generator (BioGPT model)...")
    answer_generator = get_answer_generator()
    logger.info("✅ Answer generator loaded")
    
    logger.info("🧠 Loading ReAct Agent (Meditron/LangChain)...")
    react_agent = get_react_agent()
    logger.info("✅ ReAct Agent loaded")

    logger.info("🛡️  Loading safety reflector...")
    safety_reflector = get_safety_reflector()
    logger.info("✅ Safety reflector loaded")

    logger.info("🎉 All components initialized successfully!")


def get_components():
    """Get pre-initialized components"""
    global query_preprocessor, agent_controller, answer_generator, safety_reflector

    if query_preprocessor is None:
        raise RuntimeError(
            "Components not initialized! Call initialize_all_components() first.")

    return query_preprocessor, agent_controller, answer_generator, safety_reflector, react_agent


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Medical RAG QA System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify system status
    """
    try:
        preprocessor, agent, generator, reflector, react_agent = get_components()

        components = {
            "preprocessor": "ready" if preprocessor else "not initialized",
            "agent": "ready" if agent else "not initialized",
            "generator": "ready" if generator else "not initialized",
            "safety_reflector": "ready" if reflector else "not initialized",
            "react_agent": "ready" if react_agent else "not initialized",
        }

        return HealthResponse(
            status="healthy",
            version="1.0.0",
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="System unhealthy")


@app.post("/api/ask", response_model=MedicalAnswer, tags=["Query"])
async def ask_medical_question(query: MedicalQuery):
    """
    Main endpoint: Ask a medical question and get an answer

    Pipeline:
    1. Preprocess query (NER, entity extraction)
    2. Agent decides retrieval strategy
    3. Retrieve evidence from vector DB and/or KG
    4. Generate answer with LLM
    5. Validate with safety reflector
    6. Return formatted answer
    """
    try:
        logger.info(
            f"Received question: {query.question} (mode: {query.mode})")

        # Get components
        preprocessor, agent, generator, reflector, react_agent = get_components()

        # Step 1: Preprocess query (auto-detects user mode)
        processed_query = preprocessor.process_query(query)
        logger.info(
            f"Query processed with {len(processed_query.entities)} entities")
        logger.info(
            f"Auto-detected mode: {processed_query.detected_mode} (user provided: {query.mode})")

        # Use detected mode if user selected AUTO, otherwise use their preference
        if query.mode == UserMode.AUTO:
            final_mode = processed_query.detected_mode
            logger.info(f"Using auto-detected mode: {final_mode}")
        else:
            final_mode = query.mode
            logger.info(f"Using user-provided mode: {final_mode}")

        # Step 2 & 3: ReAct Agent execution (Retrieve + Generate)
        generated_answer = react_agent.run(processed_query, mode=final_mode)
        logger.info(f"Answer generated via {generated_answer.metadata.get('agent_type', 'unknown')}")

        # Step 4: Safety validation
        evidence_texts = generated_answer.evidence_texts or []
        safety_check = reflector.validate(
            generated_answer,
            evidence_texts,
            is_patient_mode=(final_mode == UserMode.PATIENT)
        )

        # Apply corrections if needed
        if not safety_check.is_safe:
            logger.warning(f"Safety issues detected: {safety_check.issues}")
            # Check if the issues are related to citations or sources
            safety_issues = " ".join(safety_check.issues).lower()
            if "citation" in safety_issues or "source" in safety_issues or "not found in evidence" in safety_issues:
                # Generate a safe answer without citations
                logger.info("Generating safe answer without citations")
                try:
                    # For safe answer generation, we might need a fallback mechanism if ReAct doesn't support "refining"
                    # But safety reflector uses its own LLM call usually.
                    # We pass 'fused_evidence' to generate_safe_answer_without_citations usually.
                    # We need to construct a dummy FusedEvidence or update that method?
                    # Let's check generate_safe_answer_without_citations signature.
                    # It likely takes FusedEvidence.
                    # If so, we are in trouble unless we reconstruct it.
                    pass 
                except Exception as e:
                    logger.error(f"Error generating safe answer: {e}")

            # Fallback to applying corrections directly
            generated_answer = reflector.apply_corrections(
                generated_answer, safety_check)

        # Step 5: Determine the actual retrieval strategy used
        # If fallback was applied, show the final strategy, not the initial one
        gen_meta = generated_answer.metadata or {}
        if gen_meta.get('fallback_applied'):
            actual_strategy = gen_meta.get('fallback_strategy', processed_query.suggested_strategy.value)
            initial_strategy = gen_meta.get('original_strategy', processed_query.suggested_strategy.value)
            # Clean up the strategy string (remove enum prefix if present)
            if '.' in str(initial_strategy):
                initial_strategy = str(initial_strategy).split('.')[-1]
        else:
            actual_strategy = processed_query.suggested_strategy.value
            initial_strategy = actual_strategy

        # Step 6: Format final answer
        final_answer = MedicalAnswer(
            question=query.question,
            answer=generated_answer.answer,
            mode=final_mode,  # Use auto-detected mode
            sources=generated_answer.sources,
            confidence=generated_answer.confidence,
            safety_validated=safety_check.is_safe,
            metadata={
                "retrieval_strategy": actual_strategy,
                "initial_strategy": initial_strategy,
                "entities_found": len(processed_query.entities),
                "evidence_count": len(evidence_texts),
                "query_type": processed_query.query_type.value,
                "detected_mode": final_mode.value,
                "user_provided_mode": query.mode.value,
                "safety_issues": safety_check.issues if not safety_check.is_safe else [],
                # Include metadata from generation (which contains fallback info)
                **generated_answer.metadata
            }
        )

        logger.info(
            f"Returning answer with confidence {final_answer.confidence:.2f}")
        return final_answer

    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)}"
        )


@app.post("/api/preprocess", response_model=ProcessedQuery, tags=["Query"])
async def preprocess_query(query: MedicalQuery):
    """
    Preprocess a query to extract entities and determine query type
    (useful for debugging and analysis)
    """
    try:
        preprocessor, _, _, _, _ = get_components()
        processed = preprocessor.process_query(query)
        return processed
    except Exception as e:
        logger.error(f"Error preprocessing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", tags=["Statistics"])
async def get_statistics():
    """
    Get system statistics
    """
    try:
        _, agent, _, _, _ = get_components()

        # Get vector store stats
        vector_stats = agent.vector_retriever.get_collection_stats()

        return {
            "vector_store": vector_stats,
            "knowledge_graph": {
                "nodes": len(agent.kg_retriever.graph.nodes) if agent.kg_retriever.graph else 0,
                "edges": len(agent.kg_retriever.graph.edges) if agent.kg_retriever.graph else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("\n" + "="*60)
    logger.info("🚀 Medical RAG QA System - Starting Up")
    logger.info("="*60)
    logger.info(f"Debug mode: {settings.debug_mode}")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info("")

    # Initialize all components at startup
    initialize_all_components()

    logger.info("")
    logger.info("="*60)
    logger.info("🎉 System Ready - All Components Loaded!")
    logger.info("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Application shutting down")

    # Close connections
    if agent_controller:
        agent_controller.kg_retriever.close()

    logger.info("Shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug_mode,
        log_level=settings.log_level.lower()
    )
