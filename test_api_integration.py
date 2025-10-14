"""
Comprehensive API Integration Test

Tests all endpoints and features of the Medical RAG QA system:
- Health check
- Query preprocessing  
- Medical question answering
- Automatic mode detection
- Statistics
- Error handling
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30


class Colors:
    """ANSI colors for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def test_health_check() -> bool:
    """Test /api/health endpoint"""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is healthy")
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Components: {data.get('components')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running?")
        print_warning(f"Start with: python scripts/run.py")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


def test_preprocess_endpoint() -> bool:
    """Test /api/preprocess endpoint"""
    print_header("TEST 2: Query Preprocessing")
    
    test_cases = [
        {
            "question": "What is the differential diagnosis for chest pain?",
            "expected_mode": "doctor",
            "description": "Medical professional question"
        },
        {
            "question": "I have diabetes. What should I eat?",
            "expected_mode": "patient",
            "description": "Patient question with personal pronouns"
        },
        {
            "question": "What are the side effects of metformin?",
            "expected_mode": "patient",
            "description": "General patient concern"
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['description']}")
        print(f"Question: {test['question']}")
        
        try:
            payload = {
                "question": test['question'],
                "mode": "patient"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/preprocess",
                json=payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                detected_mode = data.get('detected_mode')
                query_type = data.get('query_type')
                strategy = data.get('suggested_strategy')
                entities = data.get('entities', [])
                
                print_success("Preprocessing successful")
                print(f"  Detected mode: {detected_mode}")
                print(f"  Query type: {query_type}")
                print(f"  Strategy: {strategy}")
                print(f"  Entities found: {len(entities)}")
                
                if entities:
                    print(f"  Entities:")
                    for entity in entities[:3]:
                        print(f"    - {entity['text']} ({entity['entity_type']})")
                
                # Check mode detection
                if detected_mode == test['expected_mode']:
                    print_success(f"Mode detection correct: {detected_mode}")
                else:
                    print_warning(f"Expected {test['expected_mode']}, got {detected_mode}")
                    all_passed = False
            else:
                print_error(f"Preprocessing failed: {response.status_code}")
                print(f"  Response: {response.text}")
                all_passed = False
                
        except Exception as e:
            print_error(f"Test failed: {e}")
            all_passed = False
    
    return all_passed


def test_ask_endpoint() -> bool:
    """Test /api/ask endpoint with various questions"""
    print_header("TEST 3: Medical Question Answering")
    
    test_questions = [
        {
            "question": "What is diabetes?",
            "mode": "patient",
            "description": "Basic definition question"
        },
        {
            "question": "What are the side effects of Metformin?",
            "mode": "patient",
            "description": "Drug side effects"
        },
        {
            "question": "What is the pathophysiology of Type 2 diabetes?",
            "mode": "doctor",
            "description": "Technical medical question"
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{'─' * 80}")
        print(f"Question {i}: {test['description']}")
        print(f"Q: {test['question']}")
        
        try:
            payload = {
                "question": test['question'],
                "mode": test['mode']
            }
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/ask",
                json=payload,
                timeout=TIMEOUT
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                answer = data.get('answer', '')
                mode = data.get('mode')
                sources = data.get('sources', [])
                confidence = data.get('confidence', 0)
                safety_validated = data.get('safety_validated', False)
                metadata = data.get('metadata', {})
                
                print_success(f"Answer generated in {elapsed:.2f}s")
                print(f"\n  Mode: {mode}")
                print(f"  Confidence: {confidence:.2%}")
                print(f"  Safety validated: {safety_validated}")
                print(f"  Sources: {len(sources)}")
                
                # Print answer (truncated)
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"\n  Answer:\n  {answer_preview}")
                
                # Print metadata
                print(f"\n  Metadata:")
                print(f"    Detected mode: {metadata.get('detected_mode')}")
                print(f"    Strategy: {metadata.get('retrieval_strategy')}")
                print(f"    Entities: {metadata.get('entities_found')}")
                print(f"    Evidence: {metadata.get('evidence_count')}")
                
                # Validation checks
                if not answer or len(answer) < 10:
                    print_warning("Answer seems too short")
                    all_passed = False
                
                if confidence < 0.3:
                    print_warning(f"Low confidence: {confidence:.2%}")
                
                if not safety_validated:
                    print_warning("Answer not safety validated")
                
                if sources:
                    print(f"\n  Sources:")
                    for source in sources[:3]:
                        print(f"    - {source}")
            else:
                print_error(f"Request failed: {response.status_code}")
                print(f"  Error: {response.text}")
                all_passed = False
                
        except requests.exceptions.Timeout:
            print_error(f"Request timeout (>{TIMEOUT}s)")
            print_warning("Backend may be processing, try again later")
            all_passed = False
        except Exception as e:
            print_error(f"Test failed: {e}")
            all_passed = False
    
    return all_passed


def test_statistics_endpoint() -> bool:
    """Test /api/stats endpoint"""
    print_header("TEST 4: System Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            vector_store = data.get('vector_store', {})
            kg = data.get('knowledge_graph', {})
            
            print_success("Statistics retrieved")
            print(f"\n  Vector Store:")
            print(f"    Documents: {vector_store.get('document_count', 0)}")
            print(f"    Collection: {vector_store.get('collection_name', 'N/A')}")
            print(f"    Model: {vector_store.get('embedding_model', 'N/A')}")
            
            print(f"\n  Knowledge Graph:")
            print(f"    Nodes: {kg.get('nodes', 0)}")
            print(f"    Edges: {kg.get('edges', 0)}")
            
            # Validate data
            if vector_store.get('document_count', 0) == 0:
                print_warning("Vector store appears empty")
                return False
            
            return True
        else:
            print_error(f"Statistics request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Statistics test failed: {e}")
        return False


def test_error_handling() -> bool:
    """Test error handling"""
    print_header("TEST 5: Error Handling")
    
    # Test empty question
    print("\nTest: Empty question")
    try:
        response = requests.post(
            f"{BASE_URL}/api/ask",
            json={"question": "", "mode": "patient"},
            timeout=10
        )
        
        if response.status_code == 422:  # Validation error
            print_success("Empty question properly rejected")
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
    except Exception as e:
        print_error(f"Error test failed: {e}")
        return False
    
    # Test invalid mode
    print("\nTest: Invalid mode")
    try:
        response = requests.post(
            f"{BASE_URL}/api/ask",
            json={"question": "What is diabetes?", "mode": "invalid"},
            timeout=10
        )
        
        if response.status_code == 422:  # Validation error
            print_success("Invalid mode properly rejected")
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
    except Exception as e:
        print_error(f"Error test failed: {e}")
        return False
    
    return True


def test_mode_detection_accuracy() -> bool:
    """Test automatic mode detection accuracy"""
    print_header("TEST 6: Mode Detection Accuracy")
    
    test_cases = [
        ("What is the differential diagnosis for acute MI?", "doctor"),
        ("What is the pathophysiology of hypertension?", "doctor"),
        ("What are contraindications for aspirin?", "doctor"),
        ("I have a headache, is it serious?", "patient"),
        ("Should I take my medication with food?", "patient"),
        ("My blood pressure is 140/90, what should I do?", "patient"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for question, expected_mode in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/preprocess",
                json={"question": question, "mode": "patient"},
                timeout=10
            )
            
            if response.status_code == 200:
                detected_mode = response.json().get('detected_mode')
                
                if detected_mode == expected_mode:
                    correct += 1
                    print_success(f"✓ {question[:50]}... → {detected_mode}")
                else:
                    print_warning(f"✗ {question[:50]}... → {detected_mode} (expected {expected_mode})")
        except Exception as e:
            print_error(f"Test failed: {e}")
    
    accuracy = (correct / total) * 100
    print(f"\nAccuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    if accuracy >= 80:
        print_success(f"Mode detection accuracy: {accuracy:.1f}%")
        return True
    else:
        print_warning(f"Mode detection accuracy below 80%: {accuracy:.1f}%")
        return False


def run_all_tests():
    """Run all integration tests"""
    print(f"\n{Colors.BOLD}{'=' * 80}")
    print("MEDICAL RAG QA API - INTEGRATION TESTS")
    print(f"{'=' * 80}{Colors.END}\n")
    
    print(f"Backend URL: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s\n")
    
    results = {
        "Health Check": test_health_check(),
    }
    
    # Only continue if backend is healthy
    if not results["Health Check"]:
        print_error("\nBackend not available. Please start the backend first:")
        print("  python scripts/run.py")
        return
    
    # Run remaining tests
    results["Query Preprocessing"] = test_preprocess_endpoint()
    results["Question Answering"] = test_ask_endpoint()
    results["Statistics"] = test_statistics_endpoint()
    results["Error Handling"] = test_error_handling()
    results["Mode Detection"] = test_mode_detection_accuracy()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name:.<50} {status}")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("\n✓ All tests passed! API integration working correctly.")
    else:
        print_warning(f"\n⚠ {total - passed} test(s) failed. Check output above for details.")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user.{Colors.END}")
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
