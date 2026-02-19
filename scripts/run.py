"""Quick start script - runs the complete system (frontend + backend)"""
import subprocess
import sys
import time
import os
import signal
import threading
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
    missing = []

    deps = {
        'fastapi': 'fastapi',
        'chromadb': 'chromadb',
        'networkx': 'networkx',
        'sentence_transformers': 'sentence-transformers',
        'pydantic': 'pydantic',
    }

    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        logger.error(f"✗ Missing dependencies: {', '.join(missing)}")
        logger.error("\nRun this command to install:")
        logger.error("  pip install --upgrade pip setuptools wheel")
        logger.error(
            "  pip install --force-reinstall --no-cache-dir -r requirements.txt")
        return False

    logger.info("✓ All dependencies installed")
    return True


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


def check_and_kill_existing_servers():
    """Check and kill any existing servers on ports 8000 and 5173"""
    import psutil

    killed = False

    # Check for processes using port 8000 (backend)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            connections = proc.net_connections()
            for conn in connections:
                if conn.laddr.port in [8000, 5173]:
                    logger.warning(
                        f"Killing existing process on port {conn.laddr.port}: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
                    killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if killed:
        time.sleep(2)  # Wait for processes to die
        logger.info("✓ Existing servers stopped")

    return True


def start_backend():
    """Start the FastAPI backend server"""
    logger.info("\n🚀 Starting backend server...")

    # Ensure we run uvicorn from the project root so 'backend' is importable
    project_root = Path(__file__).parent.parent

    try:
        process = subprocess.Popen([
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ], cwd=str(project_root))
        return process
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        return None


def start_frontend():
    """Start the Vite frontend development server"""
    logger.info("\n🎨 Starting frontend server...")

    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        logger.error("Frontend directory not found")
        return None

    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        logger.warning("Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=str(
                frontend_dir), check=True)
        except Exception as e:
            logger.error(f"Failed to install frontend dependencies: {e}")
            return None

    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir)
        )
        return process
    except Exception as e:
        logger.error(f"Failed to start frontend: {e}")
        return None


def cleanup_processes(backend_process, frontend_process):
    """Cleanup processes on exit"""
    logger.info("\n\n🛑 Stopping servers...")

    if backend_process:
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
            logger.info("✓ Backend stopped")
        except Exception:
            backend_process.kill()

    if frontend_process:
        try:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
            logger.info("✓ Frontend stopped")
        except Exception:
            frontend_process.kill()

    logger.info("\n✓ All servers stopped")


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

    # Check and kill existing servers
    check_and_kill_existing_servers()

    # Start both servers
    logger.info("\n" + "="*60)
    logger.info("🌐 Starting Medical RAG QA System")
    logger.info("="*60)
    logger.info("\n📍 Backend API:     http://localhost:8000")
    logger.info("📍 API Docs:        http://localhost:8000/docs")
    logger.info("📍 Frontend UI:     http://localhost:5173")
    logger.info("\n💡 Press Ctrl+C to stop both servers")
    logger.info("="*60 + "\n")

    time.sleep(2)

    # Start backend
    backend_process = start_backend()
    if not backend_process:
        logger.error("Failed to start backend. Exiting.")
        return

    # Wait a moment for backend to initialize
    time.sleep(3)
    logger.info("✓ Backend started")

    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        logger.error("Failed to start frontend.")
        cleanup_processes(backend_process, None)
        return

    # Wait a moment for frontend to initialize
    time.sleep(3)
    logger.info("✓ Frontend started")

    logger.info("\n" + "="*60)
    logger.info("🎉 SYSTEM READY!")
    logger.info("="*60)
    logger.info("\n👉 Open your browser and visit: http://localhost:5173")
    logger.info("\n" + "="*60 + "\n")

    # Keep the script running and wait for Ctrl+C
    try:
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                logger.error("Backend process died unexpectedly")
                break
            if frontend_process.poll() is not None:
                logger.error("Frontend process died unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_processes(backend_process, frontend_process)


if __name__ == "__main__":
    main()
