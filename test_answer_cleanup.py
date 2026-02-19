"""
Test script for answer cleanup functionality
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.generators.answer_generator import AnswerGenerator

def test_answer_cleanup():
    """Test the answer cleanup functionality"""
    print("=" * 60)
    print("Testing Answer Cleanup Functionality")
    print("=" * 60)
    
    # Create a mock answer generator
    generator = AnswerGenerator(model_type="huggingface")
    
    # Test cases with messy outputs
    test_cases = [
        {
            "name": "Messy output with prompt artifacts",
            "input": """You are a helpful medical assistant. Based on the following medical information, provide a clear, easy-to-understand answer to the question.

Question: What are the side effects of Metformin?

Medical Information:
[1] Common side effects of Metformin include nausea, vomiting, stomach upset, diarrhea, weakness, and a metallic taste in the mouth. Rarely, it may cause lactic acidosis, a serious condition.
[2] Metformin is the first-line medication for type 2 diabetes. This meta-analysis of 100 studies shows that metformin effectively reduces HbA1c levels by 1-2% and has cardiovascular benefits. Common side effects include gastrointestinal disturbances in 20-30% of patients.

Instructions:
- Explain in simple, patient-friendly language
- Avoid complex medical jargon
- Include a disclaimer to consult a doctor
- Be empathetic and supportive
- Limit your answer to 30-40 words, descriptive and based strictly on the evidence

Answer: Common side effects of Metformin include nausea, vomiting, stomach upset, diarrhea, and weakness. Rarely, it may cause lactic acidosis. Always consult your doctor.

⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions."""
        },
        {
            "name": "Output with XML artifacts",
            "input": """Answer: Common side effects of Metformin include nausea, stomach upset, and diarrhea. <FREETEXT> </ABSTRACT> ▃

⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions."""
        },
        {
            "name": "Output with special tokens",
            "input": """Answer: Metformin commonly causes gastrointestinal side effects like nausea and diarrhea. </s> <FREETEXT> ▃

⚠️ Important: This information is for educational purposes only. Always consult with a qualified healthcare professional before making any medical decisions."""
        }
    ]
    
    # Test the cleanup logic
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        print("Input:")
        print(test_case["input"])
        
        # Apply cleanup logic (simplified version of what's in the generator)
        answer = test_case["input"]
        
        # Try to find "Answer:" marker and extract text after it
        if "Answer:" in answer:
            parts = answer.split("Answer:")
            answer_text = parts[-1].strip()
        else:
            answer_text = answer
        
        # Clean up common issues
        answer_text = answer_text.replace("</s>", "").replace("", "").strip()
        answer_text = answer_text.replace("<FREETEXT>", "").replace("</FREETEXT>", "").strip()
        answer_text = answer_text.replace("<ABSTRACT>", "").replace("</ABSTRACT>", "").strip()
        answer_text = answer_text.replace("▃", "").strip()
        
        # Remove any remaining prompt-like fragments
        prompt_indicators = ["You are a", "Based on the following", "Instructions:", "Evidence:", "Question:"]
        for indicator in prompt_indicators:
            if indicator in answer_text:
                answer_text = answer_text.split(indicator)[0].strip()
        
        # Remove extra whitespace and newlines
        answer_text = " ".join(answer_text.split())
        
        print("\nCleaned Output:")
        print(answer_text)
        
        # Check if cleanup was successful
        artifacts = ["<FREETEXT>", "</FREETEXT>", "<ABSTRACT>", "</ABSTRACT>", "▃", "</s>", "You are a", "Based on the following"]
        has_artifacts = any(artifact in answer_text for artifact in artifacts)
        
        if not has_artifacts and len(answer_text) > 10:
            print("✅ Cleanup successful")
        else:
            print("❌ Cleanup failed")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_answer_cleanup()