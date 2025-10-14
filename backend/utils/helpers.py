"""
Utility functions for the Medical RAG QA system
"""
import re
from typing import List, Dict, Any
from loguru import logger


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep medical terminology
    text = re.sub(r'[^\w\s\-\(\)\,\.\;\:]', '', text)
    return text.strip()


def normalize_medical_term(term: str) -> str:
    """Normalize medical terminology"""
    term = term.lower().strip()
    # Remove common suffixes/prefixes
    term = re.sub(r'\(s\)$', '', term)
    return term


def calculate_weighted_confidence(scores: List[float], weights: List[float]) -> float:
    """Calculate weighted confidence score"""
    if len(scores) != len(weights):
        raise ValueError("Scores and weights must have the same length")
    
    if sum(weights) == 0:
        return 0.0
    
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    return weighted_sum / sum(weights)


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_sources(sources: List[Dict[str, Any]]) -> List[str]:
    """Format source references for display"""
    formatted = []
    for source in sources:
        if source.get("type") == "pubmed":
            formatted.append(f"PubMed: PMID{source.get('pmid', 'Unknown')}")
        elif source.get("type") == "medquad":
            formatted.append(f"MedQuAD: {source.get('category', 'Unknown')}")
        elif source.get("type") == "kg":
            formatted.append(f"Knowledge Graph: {source.get('relation', 'Unknown')}")
        else:
            formatted.append(f"{source.get('type', 'Unknown')}: {source.get('id', '')}")
    return formatted


def extract_medical_entities_simple(text: str) -> List[str]:
    """Simple keyword-based entity extraction (fallback)"""
    # Common medical term patterns
    patterns = [
        r'\b[A-Z][a-z]+(?:in|ate|ide|one|ine)\b',  # Drug names
        r'\b(?:diabetes|hypertension|infection|cancer|disease)\b',  # Conditions
    ]
    
    entities = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities.extend(matches)
    
    return list(set(entities))


def split_into_chunks(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        
        if i + chunk_size >= len(words):
            break
    
    return chunks


def deduplicate_results(results: List[Dict[str, Any]], key: str = "content") -> List[Dict[str, Any]]:
    """Remove duplicate results based on a key"""
    seen = set()
    unique_results = []
    
    for result in results:
        identifier = result.get(key, "")
        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(result)
    
    return unique_results


class LoggerSetup:
    """Setup logging configuration"""
    
    @staticmethod
    def setup(log_file: str = "./logs/app.log", level: str = "INFO"):
        """Configure logger"""
        logger.add(
            log_file,
            rotation="10 MB",
            retention="10 days",
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        )
        return logger
