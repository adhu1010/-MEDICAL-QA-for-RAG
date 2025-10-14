"""
Quick API test to verify backend is working
"""
import requests
import json

# Test the API
url = "http://localhost:8000/api/ask"

test_questions = [
    "What are the side effects of Metformin?",
    "How does Metformin work?",
    "What is the best antibiotic for sinus infection?"
]

print("Testing Medical RAG QA API")
print("=" * 60)

for question in test_questions:
    print(f"\nQ: {question}")
    
    payload = {
        "question": question,
        "mode": "patient"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: OK")
            print(f"  Confidence: {data.get('confidence', 0)*100:.1f}%")
            print(f"  Strategy: {data.get('metadata', {}).get('retrieval_strategy', 'unknown')}")
            print(f"  Evidence Count: {data.get('metadata', {}).get('evidence_count', 0)}")
            print(f"  Answer: {data.get('answer', '')[:150]}...")
            print(f"  Sources: {len(data.get('sources', []))} citations")
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  {response.text}")
            
    except Exception as e:
        print(f"✗ Connection Error: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
