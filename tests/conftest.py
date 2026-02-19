"""
Pytest configuration file
"""
import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment for testing
os.environ.setdefault("DEBUG_MODE", "True")
os.environ.setdefault("TESTING", "True")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Setup test environment automatically for all tests
    """
    # Set any test-specific environment variables
    original_env = os.environ.copy()

    # Ensure we're in test mode
    os.environ["DEBUG_MODE"] = "True"
    os.environ["TESTING"] = "True"

    yield  # This is where the test runs

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_data_dir():
    """Provide a test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_medical_question():
    """Provide a sample medical question for testing"""
    return "What is diabetes mellitus?"


@pytest.fixture
def sample_medical_answer():
    """Provide a sample medical answer for testing"""
    return "Diabetes mellitus is a group of metabolic disorders characterized by hyperglycemia."


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
