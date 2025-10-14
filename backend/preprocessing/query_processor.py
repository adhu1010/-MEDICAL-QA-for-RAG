"""
Query preprocessing and Named Entity Recognition using scispaCy
"""
from typing import List, Optional
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

from loguru import logger

from backend.models import (
    MedicalEntity, ProcessedQuery, QueryType, 
    RetrievalStrategy, MedicalQuery, UserMode
)
from backend.config import agent_config
from backend.utils import clean_text, normalize_medical_term


class QueryPreprocessor:
    """Handles query understanding, NER, and UMLS mapping"""
    
    def __init__(self, model_name: str = "en_core_sci_md"):
        """
        Initialize with scispaCy model
        
        Args:
            model_name: scispaCy model name (en_core_sci_md or en_core_sci_lg)
        """
        self.nlp = None
        self.umls_linker = None
        
        # Try to load scispaCy model
        try:
            if not SPACY_AVAILABLE:
                raise ImportError("spaCy not installed")
            
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded scispaCy model: {model_name}")
            
            # Try to load UMLS linker (optional)
            try:
                from scispacy.linking import EntityLinker
                self.umls_linker = EntityLinker(
                    resolve_abbreviations=True,
                    name="umls"
                )
                self.nlp.add_pipe(self.umls_linker)
                logger.info("UMLS entity linker loaded successfully")
            except Exception as e:
                logger.warning(f"UMLS linker not available: {e}")
                
        except (OSError, ImportError) as e:
            logger.warning(f"scispaCy model {model_name} not found: {e}")
            
            # Fallback to basic spacy
            try:
                if SPACY_AVAILABLE:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Using fallback spaCy model: en_core_web_sm")
                else:
                    raise ImportError("spaCy not available")
            except (OSError, ImportError):
                logger.warning("No spaCy model available. Using simple entity extraction")
                self.nlp = None
    
    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extract medical entities from text using NER
        
        Args:
            text: Input text
            
        Returns:
            List of MedicalEntity objects
        """
        if self.nlp:
            # Use spaCy if available
            entities = []
            doc = self.nlp(text)
            
            for ent in doc.ents:
                umls_concept = None
                
                # Try to get UMLS concept if linker is available
                if self.umls_linker and hasattr(ent._, "umls_ents"):
                    umls_ents = ent._.umls_ents
                    if umls_ents:
                        # Get the top UMLS concept
                        umls_concept = umls_ents[0][0]  # (CUI, score)
                
                entity = MedicalEntity(
                    text=ent.text,
                    entity_type=ent.label_,
                    umls_concept=umls_concept,
                    confidence=0.8  # Default confidence
                )
                entities.append(entity)
            
            logger.info(f"Extracted {len(entities)} entities from query using spaCy")
            return entities
        else:
            # Fallback: simple regex-based extraction
            logger.info("Using simple entity extraction (no spaCy available)")
            return self._simple_entity_extraction(text)
    
    def _simple_entity_extraction(self, text: str) -> List[MedicalEntity]:
        """
        Simple regex-based medical entity extraction (fallback)
        
        Args:
            text: Input text
            
        Returns:
            List of MedicalEntity objects
        """
        import re
        entities = []
        
        # Common drug name patterns (capitalized, ending in common suffixes)
        drug_patterns = [
            r'\b[A-Z][a-z]+(?:in|ate|ide|one|ine|cin|zole|pril|sartan|statin)\b',
            r'\b(?:Metformin|Amoxicillin|Doxycycline|Insulin|Aspirin)\b'
        ]
        
        # Common disease/condition patterns
        disease_patterns = [
            r'\b(?:[Tt]ype\s*[12]\s*)?[Dd]iabetes\b',
            r'\b[Hh]ypertension\b',
            r'\b[Ss]inusitis\b',
            r'\b[Ii]nfection\b',
            r'\b[Cc]ancer\b'
        ]
        
        # Extract drug entities
        for pattern in drug_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entity = MedicalEntity(
                    text=match,
                    entity_type="DRUG",
                    umls_concept=None,
                    confidence=0.7
                )
                entities.append(entity)
        
        # Extract disease entities
        for pattern in disease_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = MedicalEntity(
                    text=match,
                    entity_type="DISEASE",
                    umls_concept=None,
                    confidence=0.7
                )
                entities.append(entity)
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.text.lower() not in seen:
                seen.add(entity.text.lower())
                unique_entities.append(entity)
        
        logger.info(f"Extracted {len(unique_entities)} entities using simple extraction")
        return unique_entities
    
    def detect_user_mode(self, question: str) -> UserMode:
        """
        Automatically detect if question is from a medical professional or patient
        
        Args:
            question: User's question
            
        Returns:
            UserMode enum (DOCTOR or PATIENT)
        """
        question_lower = question.lower()
        
        # Medical professional indicators
        doctor_keywords = [
            # Medical terminology
            'differential diagnosis', 'pathophysiology', 'contraindication',
            'pharmacokinetics', 'pharmacodynamics', 'dosing regimen',
            'clinical presentation', 'etiology', 'prognosis',
            'therapeutic index', 'adverse reactions', 'drug interaction',
            
            # Clinical questions
            'in patients with', 'management of', 'treatment protocol',
            'clinical guidelines', 'evidence-based', 'first-line therapy',
            'second-line', 'adjuvant therapy', 'mechanism of action',
            
            # Professional language
            'recommended for patients', 'prescribe', 'clinical trial',
            'efficacy', 'bioavailability', 'half-life',
            'therapeutic range', 'monitoring parameters',
            
            # Specific professional phrases
            'what should i prescribe', 'appropriate treatment',
            'diagnostic criteria', 'comorbidities', 'patient presents with',
            'lab values', 'workup', 'clinical manifestations'
        ]
        
        # Patient-oriented indicators
        patient_keywords = [
            # Personal/lay language
            'i have', 'i am', 'my', 'me', 'i feel', 'i\'ve been',
            'should i', 'can i', 'is it safe for me',
            
            # Simple/lay terms
            'in simple terms', 'explain simply', 'what does this mean',
            'in plain english', 'easy to understand',
            
            # Patient concerns
            'side effects', 'is it safe', 'will it help', 'how long',
            'when should i', 'do i need', 'is this normal',
            'should i worry', 'what can i do'
        ]
        
        # Score based on keyword presence
        doctor_score = sum(1 for keyword in doctor_keywords if keyword in question_lower)
        patient_score = sum(1 for keyword in patient_keywords if keyword in question_lower)
        
        # Check for technical medical terminology (stronger indicator)
        technical_terms = [
            'pathophysiology', 'pharmacokinetics', 'contraindication',
            'differential', 'etiology', 'therapeutic index',
            'bioavailability', 'efficacy'
        ]
        
        has_technical = any(term in question_lower for term in technical_terms)
        
        # Check for personal pronouns (stronger indicator of patient)
        personal_phrases = ['i have', 'i am', 'my ', 'should i']
        has_personal = any(phrase in question_lower for phrase in personal_phrases)
        
        # Decision logic
        if has_technical:
            logger.info("Detected medical professional mode (technical terminology)")
            return UserMode.DOCTOR
        
        if has_personal:
            logger.info("Detected patient mode (personal pronouns)")
            return UserMode.PATIENT
        
        if doctor_score > patient_score and doctor_score >= 2:
            logger.info(f"Detected medical professional mode (score: {doctor_score} vs {patient_score})")
            return UserMode.DOCTOR
        
        # Default to patient mode for safety (simpler, more cautious language)
        logger.info(f"Default to patient mode (score: doctor={doctor_score}, patient={patient_score})")
        return UserMode.PATIENT
    
    def detect_query_type(self, question: str) -> QueryType:
        """
        Classify the type of medical query
        
        Args:
            question: User's question
            
        Returns:
            QueryType enum
        """
        question_lower = question.lower()
        
        # Check for definition queries
        for keyword in agent_config.DEFINITION_KEYWORDS:
            if keyword in question_lower:
                return QueryType.DEFINITION
        
        # Check for complex queries
        for keyword in agent_config.COMPLEX_KEYWORDS:
            if keyword in question_lower:
                return QueryType.COMPLEX
        
        # Check for contextual queries
        for keyword in agent_config.CONTEXTUAL_KEYWORDS:
            if keyword in question_lower:
                return QueryType.CONTEXTUAL
        
        # Default to contextual
        return QueryType.CONTEXTUAL
    
    def suggest_retrieval_strategy(self, query_type: QueryType, entities: List[MedicalEntity]) -> RetrievalStrategy:
        """
        Suggest optimal retrieval strategy based on query analysis
        
        Args:
            query_type: Type of query
            entities: Extracted entities
            
        Returns:
            RetrievalStrategy enum
        """
        # Definition queries work well with KG
        if query_type == QueryType.DEFINITION and len(entities) > 0:
            return RetrievalStrategy.KG_ONLY
        
        # Complex queries benefit from hybrid approach
        if query_type == QueryType.COMPLEX:
            return RetrievalStrategy.HYBRID
        
        # Contextual queries with entities use hybrid
        if len(entities) >= 2:
            return RetrievalStrategy.HYBRID
        
        # Default to vector search for general queries
        return RetrievalStrategy.VECTOR_ONLY
    
    def normalize_query(self, question: str) -> str:
        """
        Normalize and clean the query
        
        Args:
            question: Original question
            
        Returns:
            Normalized question
        """
        # Clean text
        normalized = clean_text(question)
        
        # Remove question words for better matching
        normalized = normalized.replace("?", "")
        
        return normalized
    
    def process_query(self, query: MedicalQuery) -> ProcessedQuery:
        """
        Complete query processing pipeline
        
        Args:
            query: MedicalQuery object
            
        Returns:
            ProcessedQuery with entities, mode, and metadata
        """
        logger.info(f"Processing query: {query.question}")
        
        # Auto-detect user mode (can override manual mode if specified)
        detected_mode = self.detect_user_mode(query.question)
        
        # Use provided mode if explicitly set, otherwise use detected mode
        final_mode = query.mode if query.mode else detected_mode
        
        logger.info(f"Mode: provided={query.mode}, detected={detected_mode}, final={final_mode}")
        
        # Extract entities
        entities = self.extract_entities(query.question)
        
        # Detect query type
        query_type = self.detect_query_type(query.question)
        
        # Suggest retrieval strategy
        strategy = self.suggest_retrieval_strategy(query_type, entities)
        
        # Normalize query
        normalized = self.normalize_query(query.question)
        
        processed = ProcessedQuery(
            original_question=query.question,
            normalized_question=normalized,
            entities=entities,
            query_type=query_type,
            suggested_strategy=strategy,
            detected_mode=final_mode
        )
        
        logger.info(
            f"Query processed - Type: {query_type}, "
            f"Strategy: {strategy}, Mode: {final_mode}, Entities: {len(entities)}"
        )
        
        return processed


# Singleton instance
_preprocessor_instance = None


def get_query_preprocessor() -> QueryPreprocessor:
    """Get or create QueryPreprocessor singleton"""
    global _preprocessor_instance
    if _preprocessor_instance is None:
        _preprocessor_instance = QueryPreprocessor()
    return _preprocessor_instance
