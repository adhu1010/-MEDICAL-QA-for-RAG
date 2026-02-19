#!/bin/bash

# Medical RAG QA System - Development Start Script
# Starts both frontend and backend servers

set -e

echo "==========================================="
echo "Medical RAG QA System - Development Mode"
echo "==========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the medical-rag-qa root directory"
    exit 1
fi

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Install backend dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
fi

echo "✓ Dependencies installed"
echo ""

# Check if concurrently is installed
if ! npm list concurrently > /dev/null 2>&1; then
    echo "Installing concurrently for parallel execution..."
    npm install --save-dev concurrently
fi

echo "==========================================="
echo "Starting Development Servers"
echo "==========================================="
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Run both servers
# Run both servers without auto-reload to prevent model reloading loops
npm run start
