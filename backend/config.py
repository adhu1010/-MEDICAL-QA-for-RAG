"""
Configuration settings for Medical RAG QA System
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    huggingface_api_key: Optional[str] = Field(None, env="HUGGINGFACE_API_KEY")
    
    # Neo4j Configuration
    neo4j_uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field("neo4j", env="NEO4J_USER")
    neo4j_password: str = Field("password", env="NEO4J_PASSWORD")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = Field(default_factory=lambda: Path("./data"))
    vector_store_path: Path = Field(default_factory=lambda: Path("./vector_store"))
    medquad_path: Path = Field(default_factory=lambda: Path("./data/medquad"))
    pubmed_path: Path = Field(default_factory=lambda: Path("./data/pubmed"))
    umls_path: Path = Field(default_factory=lambda: Path("./data/umls"))
    log_file: Path = Field(default_factory=lambda: Path("./logs/app.log"))
    
    # Model Configuration
    embedding_model: str = Field("dmis-lab/biobert-base-cased-v1.2", env="EMBEDDING_MODEL")
    llm_model: str = Field("microsoft/BioGPT-Large", env="LLM_MODEL")  # BioGPT for medical domain
    llm_temperature: float = Field(0.3, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(512, env="LLM_MAX_TOKENS")
    
    # Retrieval Settings
    top_k_vector: int = Field(5, env="TOP_K_VECTOR")
    top_k_kg: int = Field(3, env="TOP_K_KG")
    similarity_threshold: float = Field(0.5, env="SIMILARITY_THRESHOLD")
    
    # Safety Settings
    enable_safety_reflection: bool = Field(True, env="ENABLE_SAFETY_REFLECTION")
    enable_content_filter: bool = Field(True, env="ENABLE_CONTENT_FILTER")
    
    # Application Settings
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    debug_mode: bool = Field(True, env="DEBUG_MODE")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # CORS Settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


# Agent Configuration
class AgentConfig:
    """Configuration for the agent decision-making"""
    
    # Query type detection keywords
    DEFINITION_KEYWORDS = ["what is", "define", "definition", "meaning of", "explain"]
    CONTEXTUAL_KEYWORDS = ["how", "why", "best", "recommend", "side effect", "treatment"]
    COMPLEX_KEYWORDS = ["compare", "difference", "multiple", "combination", "interact"]
    
    # Retrieval strategies
    STRATEGY_KG_ONLY = "kg_only"
    STRATEGY_VECTOR_ONLY = "vector_only"
    STRATEGY_SPARSE_ONLY = "sparse_only"
    STRATEGY_DENSE_SPARSE = "dense_sparse"
    STRATEGY_HYBRID = "hybrid"  # Legacy: KG + Dense
    STRATEGY_FULL_HYBRID = "full_hybrid"  # KG + Dense + Sparse
    
    # Confidence thresholds
    KG_CONFIDENCE_THRESHOLD = 0.8
    VECTOR_CONFIDENCE_THRESHOLD = 0.7
    SPARSE_CONFIDENCE_THRESHOLD = 0.6
    
    # Fusion weights (for weighted fusion method)
    FUSION_WEIGHT_KG = 0.5
    FUSION_WEIGHT_VECTOR = 0.3  # Dense
    FUSION_WEIGHT_SPARSE = 0.2  # BM25
    
    # RRF constant for Reciprocal Rank Fusion
    RRF_K = 60  # Standard value used in literature


agent_config = AgentConfig()
