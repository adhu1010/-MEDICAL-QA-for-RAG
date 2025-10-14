"""
Safety reflection and validation layer
"""
import re
from typing import List
from loguru import logger

from backend.models import GeneratedAnswer, SafetyCheck
from backend.config import settings


class SafetyReflector:
    """
    Validates generated answers for safety and accuracy
    """
    
    # Potentially harmful patterns
    HARMFUL_PATTERNS = [
        r"you should take \d+",  # Specific dosage recommendations
        r"take exactly",
        r"guaranteed to cure",
        r"definitely will",
        r"no need to see a doctor",
        r"stop taking your medication",
    ]
    
    # Required disclaimer phrases for patient mode
    REQUIRED_DISCLAIMERS = [
        "consult",
        "healthcare",
        "doctor",
        "physician",
        "medical professional"
    ]
    
    # Hallucination indicators
    HALLUCINATION_INDICATORS = [
        r"according to my knowledge",
        r"i believe",
        r"probably",
        r"might be",
        r"could possibly"
    ]
    
    def __init__(self):
        """Initialize safety reflector"""
        logger.info("Safety reflector initialized")
    
    def check_harmful_content(self, answer: str) -> List[str]:
        """
        Check for potentially harmful medical advice
        
        Args:
            answer: Generated answer text
            
        Returns:
            List of issues found
        """
        issues = []
        answer_lower = answer.lower()
        
        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, answer_lower):
                issues.append(f"Contains potentially harmful advice: {pattern}")
        
        return issues
    
    def check_disclaimer(self, answer: str, is_patient_mode: bool) -> List[str]:
        """
        Check if appropriate disclaimers are present
        
        Args:
            answer: Generated answer text
            is_patient_mode: Whether this is patient mode
            
        Returns:
            List of issues found
        """
        issues = []
        
        if not is_patient_mode:
            return issues
        
        answer_lower = answer.lower()
        
        # Check if at least one disclaimer phrase is present
        has_disclaimer = any(
            phrase in answer_lower
            for phrase in self.REQUIRED_DISCLAIMERS
        )
        
        if not has_disclaimer:
            issues.append("Missing required medical disclaimer for patient mode")
        
        return issues
    
    def check_hallucination_indicators(self, answer: str) -> List[str]:
        """
        Check for signs of hallucinated content
        
        Args:
            answer: Generated answer text
            
        Returns:
            List of issues found
        """
        issues = []
        answer_lower = answer.lower()
        
        for pattern in self.HALLUCINATION_INDICATORS:
            if re.search(pattern, answer_lower):
                issues.append(f"Potential hallucination indicator: {pattern}")
        
        return issues
    
    def check_evidence_alignment(
        self,
        answer: str,
        evidence_texts: List[str]
    ) -> List[str]:
        """
        Check if answer aligns with provided evidence
        
        Args:
            answer: Generated answer
            evidence_texts: List of evidence content
            
        Returns:
            List of issues found
        """
        issues = []
        
        # Simple check: extract medical terms from answer and verify in evidence
        # Extract potential drug names (capitalized words ending in common suffixes)
        drug_pattern = r'\b[A-Z][a-z]+(?:in|ate|ide|one|ine|cin)\b'
        mentioned_drugs = set(re.findall(drug_pattern, answer))
        
        # Check if mentioned drugs appear in evidence
        evidence_combined = " ".join(evidence_texts).lower()
        
        for drug in mentioned_drugs:
            if drug.lower() not in evidence_combined:
                issues.append(f"Drug '{drug}' mentioned but not found in evidence")
        
        return issues
    
    def suggest_improvements(self, issues: List[str]) -> List[str]:
        """
        Suggest improvements based on identified issues
        
        Args:
            issues: List of issues found
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        for issue in issues:
            if "harmful advice" in issue:
                suggestions.append("Remove specific dosage recommendations and suggest consulting a doctor")
            
            if "disclaimer" in issue:
                suggestions.append("Add a disclaimer: 'Always consult with a healthcare professional'")
            
            if "hallucination" in issue:
                suggestions.append("Rephrase with more certainty based on evidence, or remove uncertain statements")
            
            if "not found in evidence" in issue:
                suggestions.append("Remove or verify claims not supported by retrieved evidence")
        
        return suggestions
    
    def validate(
        self,
        answer: GeneratedAnswer,
        evidence_texts: List[str],
        is_patient_mode: bool = True
    ) -> SafetyCheck:
        """
        Perform complete safety validation
        
        Args:
            answer: Generated answer
            evidence_texts: Evidence content used for generation
            is_patient_mode: Whether in patient mode
            
        Returns:
            SafetyCheck result
        """
        if not settings.enable_safety_reflection:
            logger.info("Safety reflection disabled")
            return SafetyCheck(is_safe=True, issues=[], suggestions=[])
        
        logger.info("Performing safety validation")
        
        all_issues = []
        
        # Run all checks
        all_issues.extend(self.check_harmful_content(answer.answer))
        all_issues.extend(self.check_disclaimer(answer.answer, is_patient_mode))
        all_issues.extend(self.check_hallucination_indicators(answer.answer))
        all_issues.extend(self.check_evidence_alignment(answer.answer, evidence_texts))
        
        # Generate suggestions
        suggestions = self.suggest_improvements(all_issues)
        
        # Determine if safe
        # Critical issues make it unsafe
        critical_keywords = ["harmful", "not found in evidence"]
        has_critical_issue = any(
            any(keyword in issue.lower() for keyword in critical_keywords)
            for issue in all_issues
        )
        
        is_safe = not has_critical_issue
        
        logger.info(
            f"Safety validation complete: {'SAFE' if is_safe else 'UNSAFE'}, "
            f"{len(all_issues)} issues found"
        )
        
        return SafetyCheck(
            is_safe=is_safe,
            issues=all_issues,
            suggestions=suggestions
        )
    
    def apply_corrections(
        self,
        answer: GeneratedAnswer,
        safety_check: SafetyCheck
    ) -> GeneratedAnswer:
        """
        Apply automatic corrections based on safety check
        
        Args:
            answer: Original answer
            safety_check: Safety check results
            
        Returns:
            Corrected answer
        """
        if safety_check.is_safe:
            return answer
        
        logger.info("Applying safety corrections")
        
        corrected_text = answer.answer
        
        # Remove harmful patterns
        for pattern in self.HARMFUL_PATTERNS:
            corrected_text = re.sub(pattern, "[medical advice redacted - consult doctor]", corrected_text, flags=re.IGNORECASE)
        
        # Add disclaimer if missing
        if "disclaimer" in " ".join(safety_check.issues).lower():
            corrected_text += "\n\n⚠️ Important: Always consult with a qualified healthcare professional for medical advice."
        
        return GeneratedAnswer(
            answer=corrected_text,
            confidence=answer.confidence * 0.8,  # Reduce confidence due to corrections
            sources=answer.sources,
            reasoning=answer.reasoning + " [Safety corrections applied]"
        )


# Singleton instance
_reflector_instance = None


def get_safety_reflector() -> SafetyReflector:
    """Get or create SafetyReflector singleton"""
    global _reflector_instance
    if _reflector_instance is None:
        _reflector_instance = SafetyReflector()
    return _reflector_instance
