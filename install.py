"""
Simple installation script that requires no dependencies
Run this first to install all required packages
"""
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print welcome banner"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  🩺 Medical RAG QA System - Installation               ║
    ║  Step 1: Installing Python dependencies                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)


def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ ERROR: Python 3.9+ required, you have {version.major}.{version.minor}")
        print("Please upgrade Python and try again")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def install_requirements():
    """Install requirements.txt"""
    base_dir = Path(__file__).parent
    req_file = base_dir / "requirements.txt"
    req_minimal = base_dir / "requirements-minimal.txt"
    
    if not req_file.exists():
        print(f"❌ ERROR: requirements.txt not found at {req_file}")
        return False
    
    print("\n📦 Installing Python packages from requirements.txt...")
    print("This may take several minutes...\n")
    
    try:
        # Try full requirements first
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("✓ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("⚠️ Full installation failed. Trying minimal installation...\n")
        
        # Try minimal requirements as fallback
        if req_minimal.exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_minimal)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(result.stdout)
                print("✓ Minimal packages installed successfully!")
                print("\n⚠️ Note: Some advanced features may not work without full installation")
                print("You can install missing packages manually later.")
                return True
                
            except subprocess.CalledProcessError as e2:
                print(f"❌ ERROR: Even minimal installation failed:")
                print(e2.stdout)
                print(e2.stderr)
                return False
        else:
            print(f"❌ ERROR installing packages:")
            print(e.stdout)
            print(e.stderr)
            return False


def install_scispacy():
    """Install scispaCy model"""
    print("\n🧠 Installing scispaCy medical NLP model...")
    print("This may take a few minutes...\n")
    
    scispacy_url = "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz"
    
    response = input("Download scispaCy model (~100MB)? (y/n): ")
    if response.lower() != 'y':
        print("⚠️ Skipping scispaCy model (you can install it later)")
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", scispacy_url],
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ scispaCy model installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("⚠️ Failed to install scispaCy model")
        print("You can install it manually later with:")
        print(f"  pip install {scispacy_url}")
        return True  # Non-critical, continue anyway


def main():
    """Main installation process"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed!")
        print("\nTry manually:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Install scispaCy model
    install_scispacy()
    
    # Success message
    print("\n" + "="*60)
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✓ Installation Complete!                                ║
    ╚══════════════════════════════════════════════════════════╝
    
    🎉 All dependencies installed successfully!
    
    📋 Next Steps:
    
    1. Configure environment (optional):
       - Copy .env.example to .env
       - Edit .env to add API keys if needed
    
    2. Prepare data:
       python scripts/download_data.py
       python scripts/build_vector_store.py
       python scripts/build_knowledge_graph.py
    
       Or run the setup script:
       python scripts/setup.py
    
    3. Start the application:
       python scripts/run.py
       
       Or manually:
       uvicorn backend.main:app --reload
    
    4. Open the frontend:
       Open frontend/index.html in your browser
       Or visit http://localhost:8000/docs
    
    📚 Documentation:
       - README.md - Project overview
       - SETUP_GUIDE.md - Detailed setup instructions
       - QUICK_REFERENCE.md - Quick commands
    
    ⚠️ Remember: This is for educational/research purposes only!
    """)
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
