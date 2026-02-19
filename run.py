import subprocess
import sys
import os
import time
import signal
import platform

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Global process list for cleanup
processes = []

def cleanup_processes(signum=None, frame=None):
    print("\n🛑 Stopping services...")
    for p in processes:
        try:
            if p.poll() is None: # Only kill if still running
                if platform.system() == "Windows":
                     subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
                else:
                    # Kill the process group to ensure children (like npm->vite) are also killed
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass
    print("✓ Stopped.")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup_processes)
signal.signal(signal.SIGTERM, cleanup_processes)

def run_service(command, cwd=None, name="Service", env=None):
    print(f"🚀 Starting {name}...")
    
    # Use setsid on Unix to create a process group
    kw = {}
    if platform.system() != "Windows":
        kw['preexec_fn'] = os.setsid
    
    # Merge environment variables
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
        
    process = subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        env=proc_env,
        **kw
    )
    return process

def main():
    print("===========================================")
    print("   Medical RAG QA - Launcher")
    print("===========================================")
    print(f"📂 Project Root: {PROJECT_ROOT}")

    try:
        # 1. Start Backend
        # robustly find uvicorn by running it as a python module from the CURRENT interpreter
        # This ensures we use the active venv even inside the subprocess
        python_exe = sys.executable
        backend_cmd = f"{python_exe} -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
        
        # Check for dev argument
        if len(sys.argv) > 1 and sys.argv[1] == 'dev':
            print("⚠️  Dev mode enabled: Backend will auto-reload on changes")
            backend_cmd += " --reload"
        else:
            print("ℹ️  Standard mode: Models load once (faster startup)")
            
        print(f"📝 Backend Command: {backend_cmd}")
            
        backend = run_service(backend_cmd, cwd=PROJECT_ROOT, name="Backend (FastAPI)")
        processes.append(backend)

        # Allow backend a moment to start initializing
        time.sleep(2)
        
        if backend.poll() is not None:
             print("❌ Backend failed to start immediately. Check logs above.")
             raise RuntimeError("Backend startup failed")

        # 2. Start Frontend
        frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
        print(f"📝 Frontend Directory: {frontend_dir}")
        frontend = run_service("npm run dev", cwd=frontend_dir, name="Frontend (Vite)")
        processes.append(frontend)

        print("\n✅ Services are starting...")
        print(f"Backend API: http://localhost:{BACKEND_PORT}")
        print(f"Frontend UI: http://localhost:{FRONTEND_PORT} (or next available port)\n")
        print("Press Ctrl+C to stop everything.\n")

        # Keep main thread alive
        while True:
            time.sleep(1)
            # Check if processes are still alive and print exit codes if they died
            if backend.poll() is not None:
                print(f"\n❌ Backend stopped unexpectedly with code {backend.returncode}.")
                break
            if frontend.poll() is not None:
                print(f"\n❌ Frontend stopped unexpectedly with code {frontend.returncode}.")
                break

    except KeyboardInterrupt:
        cleanup_processes()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        cleanup_processes()

if __name__ == "__main__":
    main()
