"""
Quick start script - runs the complete system
"""
import subprocess
import sys
import time
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    class SimpleLogger:
        def info(self, msg): print(msg)
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    logger = SimpleLogger()


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import chromadb
        import networkx
        logger.info("✓ Dependencies check passed")
        return True
    except ImportError as e:
        logger.error(f"✗ Missing dependency: {e}")
        logger.error("Run: pip install -r requirements.txt")
        return False


def check_data():
    """Check if data is prepared"""
    data_dir = Path(__file__).parent.parent / "data"
    medquad = data_dir / "medquad" / "sample_qa_pairs.json"
    
    if not medquad.exists():
        logger.warning("⚠️ Sample data not found")
        logger.info("Run: python scripts/download_data.py")
        return False
    
    logger.info("✓ Data check passed")
    return True


def start_backend():
    """Start the FastAPI backend server"""
    logger.info("\n🚀 Starting backend server...")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        logger.info("\n\n✓ Server stopped")


def main():
    """Main run script"""
    logger.info("""
    ╔══════════════════════════════════════════════════════════╗
    ║  🩺 Medical RAG QA System - Quick Start                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Checks
    if not check_dependencies():
        logger.error("Please install dependencies first:")
        logger.error("  pip install -r requirements.txt")
        return
    
    if not check_data():
        logger.warning("Data not prepared. System may not work properly.")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            logger.info("Run setup script first: python scripts/setup.py")
            return
    
    # Start server
    logger.info("\n📍 Backend will be available at: http://localhost:8000")
    logger.info("📍 API docs will be at: http://localhost:8000/docs")
    logger.info("📍 Frontend: Open frontend/index.html in your browser")
    logger.info("\n" + "="*60 + "\n")
    
    time.sleep(2)
    start_backend()


if __name__ == "__main__":
    main()
