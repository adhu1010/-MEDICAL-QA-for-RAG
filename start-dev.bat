@echo off
REM Medical RAG QA System - Development Start Script for Windows
REM Starts both frontend and backend servers

setlocal enabledelayedexpansion

echo ===========================================
echo Medical RAG QA System - Development Mode
echo ===========================================
echo.

REM Check if we're in the right directory
if not exist "package.json" (
    echo Error: Please run this script from the medical-rag-qa root directory
    exit /b 1
)

if not exist "requirements.txt" (
    echo Error: requirements.txt not found. Please run from medical-rag-qa root directory
    exit /b 1
)

REM Check Node.js installation
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed or not in PATH
    exit /b 1
)

REM Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo ✓ Prerequisites check passed
echo.

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

REM Install backend dependencies if needed
python -c "import fastapi" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
)

echo ✓ Dependencies installed
echo.

REM Check if concurrently is installed
npm list concurrently >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing concurrently for parallel execution...
    call npm install --save-dev concurrently
)

echo ===========================================
echo Starting Development Servers
echo ===========================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop all servers
echo.

REM Run both servers
call npm run dev:full

endlocal
