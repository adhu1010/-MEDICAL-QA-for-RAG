"""
Test automatic user mode detection

This script demonstrates how the system automatically detects whether
a question is from a medical professional or a patient.
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/ask"

# Test cases
test_questions = [
    {
        "category": "Medical Professional Questions",
        "questions": [
            "What is the differential diagnosis for a patient presenting with acute chest pain and dyspnea?",
            "What are the contraindications for prescribing metformin in patients with renal dysfunction?",
            "Explain the pathophysiology of type 2 diabetes mellitus.",
            "What is the first-line therapy for hypertension management?",
            "Describe the pharmacokinetics of amoxicillin in elderly patients.",
            "What are the clinical manifestations of bacterial sinusitis versus viral sinusitis?",
            "What therapeutic index should I consider when prescribing warfarin?",
        ]
    },
    {
        "category": "Patient Questions",
        "questions": [
            "I have diabetes. What foods should I avoid?",
            "Is it safe for me to take aspirin daily?",
            "I feel dizzy after taking my blood pressure medication. What should I do?",
            "Can I drink alcohol while on antibiotics?",
            "What are the side effects of metformin?",
            "Should I worry about chest pain after exercise?",
            "How long does it take for amoxicillin to work?",
            "Is headache normal with my new medication?",
        ]
    },
    {
        "category": "General/Ambiguous Questions",
        "questions": [
            "What is diabetes?",
            "How does metformin work?",
            "What causes high blood pressure?",
            "Tell me about antibiotics.",
        ]
    }
]


def test_mode_detection():
    """Test automatic mode detection for various questions"""
    
    print("=" * 80)
    print("AUTOMATIC USER MODE DETECTION TEST")
    print("=" * 80)
    print()
    
    for test_group in test_questions:
        print(f"\n{test_group['category']}:")
        print("-" * 80)
        
        for question in test_group['questions']:
            print(f"\nQuestion: {question}")
            
            # Send request with default patient mode
            # (system will auto-detect the actual mode)
            payload = {
                "question": question,
                "mode": "patient"  # Default, will be overridden
            }
            
            try:
                response = requests.post(API_URL, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    detected_mode = result['metadata'].get('detected_mode', 'unknown')
                    provided_mode = result['metadata'].get('user_provided_mode', 'unknown')
                    
                    print(f"  User provided mode: {provided_mode}")
                    print(f"  Auto-detected mode: {detected_mode}")
                    
                    if detected_mode != provided_mode:
                        print(f"  ✓ Mode CHANGED from {provided_mode} to {detected_mode}")
                    else:
                        print(f"  ✓ Mode SAME as provided")
                    
                    # Show snippet of answer
                    answer_snippet = result['answer'][:150] + "..." if len(result['answer']) > 150 else result['answer']
                    print(f"  Answer: {answer_snippet}")
                    
                else:
                    print(f"  ❌ Error: {response.status_code}")
                    print(f"     {response.text}")
            
            except Exception as e:
                print(f"  ❌ Request failed: {e}")
        
        print()


def test_preprocess_endpoint():
    """Test the preprocess endpoint to see mode detection"""
    
    print("\n" + "=" * 80)
    print("PREPROCESS ENDPOINT TEST (Shows detection details)")
    print("=" * 80)
    
    test_cases = [
        ("What is the differential diagnosis for acute chest pain?", "Expected: DOCTOR"),
        ("I have a headache. Is this serious?", "Expected: PATIENT"),
        ("What is diabetes?", "Expected: PATIENT (default)"),
    ]
    
    for question, expected in test_cases:
        print(f"\nQuestion: {question}")
        print(f"{expected}")
        
        payload = {
            "question": question,
            "mode": "patient"
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/api/preprocess",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"  Detected mode: {result['detected_mode']}")
                print(f"  Query type: {result['query_type']}")
                print(f"  Strategy: {result['suggested_strategy']}")
                print(f"  Entities: {len(result['entities'])}")
                
                if result['entities']:
                    print(f"  Found entities:")
                    for entity in result['entities'][:3]:
                        print(f"    - {entity['text']} ({entity['entity_type']})")
            else:
                print(f"  ❌ Error: {response.status_code}")
        
        except Exception as e:
            print(f"  ❌ Request failed: {e}")


if __name__ == "__main__":
    print("\n🧪 Testing Automatic User Mode Detection")
    print("\nThis test demonstrates how the system automatically analyzes")
    print("questions to determine if they're from a doctor or patient.\n")
    
    input("Press Enter to start testing (make sure backend is running)...")
    
    # Test main endpoint
    test_mode_detection()
    
    # Test preprocess endpoint for details
    print("\n" + "=" * 80)
    input("\nPress Enter to test preprocess endpoint...")
    test_preprocess_endpoint()
    
    print("\n" + "=" * 80)
    print("✓ Testing complete!")
    print("=" * 80)
