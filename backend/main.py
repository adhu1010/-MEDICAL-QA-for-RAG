"""
Main FastAPI application for Medical RAG QA System
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from backend.config import settings
from backend.models import (
    MedicalQuery, MedicalAnswer, HealthResponse,
    ProcessedQuery, UserMode
)
from backend.preprocessing import get_query_preprocessor
from backend.agents import get_agent_controller
from backend.generators import get_answer_generator
from backend.safety import get_safety_reflector
from backend.utils import LoggerSetup, format_sources

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

# Initialize components (lazy loading)
query_preprocessor = None
agent_controller = None
answer_generator = None
safety_reflector = None


def get_components():
    """Initialize all components (lazy loading)"""
    global query_preprocessor, agent_controller, answer_generator, safety_reflector
    
    if query_preprocessor is None:
        query_preprocessor = get_query_preprocessor()
        agent_controller = get_agent_controller()
        answer_generator = get_answer_generator()
        safety_reflector = get_safety_reflector()
    
    return query_preprocessor, agent_controller, answer_generator, safety_reflector


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
        preprocessor, agent, generator, reflector = get_components()
        
        components = {
            "preprocessor": "ready" if preprocessor else "not initialized",
            "agent": "ready" if agent else "not initialized",
            "generator": "ready" if generator else "not initialized",
            "safety_reflector": "ready" if reflector else "not initialized",
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
        logger.info(f"Received question: {query.question} (mode: {query.mode})")
        
        # Get components
        preprocessor, agent, generator, reflector = get_components()
        
        # Step 1: Preprocess query (auto-detects user mode)
        processed_query = preprocessor.process_query(query)
        logger.info(f"Query processed with {len(processed_query.entities)} entities")
        logger.info(f"Auto-detected mode: {processed_query.detected_mode} (user provided: {query.mode})")
        
        # Use detected mode for better accuracy
        final_mode = processed_query.detected_mode
        
        # Step 2: Agent retrieval
        fused_evidence = agent.execute(processed_query)
        logger.info(f"Retrieved {len(fused_evidence.evidences)} evidences")
        
        # Step 3: Generate answer with auto-detected mode
        generated_answer = generator.generate(
            processed_query,
            fused_evidence,
            mode=final_mode
        )
        logger.info("Answer generated")
        
        # Step 4: Safety validation
        evidence_texts = [ev.content for ev in fused_evidence.evidences]
        safety_check = reflector.validate(
            generated_answer,
            evidence_texts,
            is_patient_mode=(final_mode == UserMode.PATIENT)
        )
        
        # Apply corrections if needed
        if not safety_check.is_safe:
            logger.warning(f"Safety issues detected: {safety_check.issues}")
            generated_answer = reflector.apply_corrections(generated_answer, safety_check)
        
        # Step 5: Format final answer
        final_answer = MedicalAnswer(
            question=query.question,
            answer=generated_answer.answer,
            mode=final_mode,  # Use auto-detected mode
            sources=generated_answer.sources,
            confidence=generated_answer.confidence,
            safety_validated=safety_check.is_safe,
            metadata={
                "retrieval_strategy": processed_query.suggested_strategy.value,
                "entities_found": len(processed_query.entities),
                "evidence_count": len(fused_evidence.evidences),
                "query_type": processed_query.query_type.value,
                "detected_mode": final_mode.value,
                "user_provided_mode": query.mode.value,
                "safety_issues": safety_check.issues if not safety_check.is_safe else []
            }
        )
        
        logger.info(f"Returning answer with confidence {final_answer.confidence:.2f}")
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
        preprocessor, _, _, _ = get_components()
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
        _, agent, _, _ = get_components()
        
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
    logger.info("Application startup complete")
    logger.info(f"Debug mode: {settings.debug_mode}")
    logger.info(f"CORS origins: {settings.cors_origins}")


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
