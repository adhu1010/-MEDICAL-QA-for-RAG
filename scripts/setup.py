"""
Complete setup script for Medical RAG QA System
"""
import subprocess
import sys
from pathlib import Path

# Use print instead of logger for setup script (before dependencies installed)
try:
    from loguru import logger
    USE_LOGGER = True
except ImportError:
    USE_LOGGER = False
    class SimpleLogger:
        def info(self, msg):
            print(msg)
        def error(self, msg):
            print(f"ERROR: {msg}")
    logger = SimpleLogger()


def run_command(command, description):
    """Run a command and handle errors"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Step: {description}")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False


def main():
    """Main setup process"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Medical RAG QA System - Setup Script                   ║
    ║  This will set up your development environment           ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    base_dir = Path(__file__).parent.parent
    
    # Step 1: Create virtual environment (optional)
    logger.info("\n📦 Step 1: Virtual Environment")
    logger.info("Recommended: Create a virtual environment")
    logger.info("Run: python -m venv venv")
    logger.info("Activate: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Linux/Mac)")
    
    # Step 2: Install dependencies
    if input("\n📥 Install Python dependencies? (y/n): ").lower() == 'y':
        success = run_command(
            "pip install -r requirements.txt",
            "Installing Python packages"
        )
        if not success:
            logger.error("Failed to install dependencies")
            return
    
    # Step 3: Download spaCy model
    if input("\n🧠 Download scispaCy model? (y/n): ").lower() == 'y':
        logger.info("Downloading scispaCy model (this may take a while)...")
        run_command(
            "pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz",
            "Installing scispaCy model"
        )
    
    # Step 4: Create .env file
    if input("\n⚙️ Create .env configuration file? (y/n): ").lower() == 'y':
        env_file = base_dir / ".env"
        env_example = base_dir / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            logger.info(f"✓ Created .env file at {env_file}")
            logger.info("Please edit .env to add your API keys if needed")
        else:
            logger.info(".env file already exists")
    
    # Step 5: Download sample data
    if input("\n📊 Download sample medical data? (y/n): ").lower() == 'y':
        run_command(
            "python scripts/download_data.py",
            "Downloading sample data"
        )
    
    # Step 6: Build vector store
    if input("\n🗃️ Build vector store? (y/n): ").lower() == 'y':
        run_command(
            "python scripts/build_vector_store.py",
            "Building vector store"
        )
    
    # Step 7: Build knowledge graph
    if input("\n🕸️ Build knowledge graph? (y/n): ").lower() == 'y':
        run_command(
            "python scripts/build_knowledge_graph.py",
            "Building knowledge graph"
        )
    
    # Final message
    logger.info("""
    
    ╔══════════════════════════════════════════════════════════╗
    ║  ✓ Setup Complete!                                       ║
    ╚══════════════════════════════════════════════════════════╝
    
    🚀 Next Steps:
    
    1. Review and edit .env file with your API keys
    
    2. Start the backend server:
       python backend/main.py
       or
       uvicorn backend.main:app --reload
    
    3. Open frontend in browser:
       Open frontend/index.html in your browser
       or serve it with: python -m http.server 3000 --directory frontend
    
    4. Test the API:
       Visit http://localhost:8000/docs for API documentation
    
    📚 Documentation:
       - README.md for project overview
       - API docs at http://localhost:8000/docs
       - Frontend at http://localhost:3000 (if serving)
    
    ⚠️ Important:
       - This is for educational/research purposes only
       - Not for production medical use
       - Always verify with healthcare professionals
    """)


if __name__ == "__main__":
    main()
