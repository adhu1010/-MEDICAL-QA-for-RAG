#!/bin/bash

# Meditron Integration Verification Script
# Tests the Medical RAG QA system with both BioGPT and Ollama backends

echo "========================================="
echo "Meditron Integration Verification"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is running
echo "1. Checking if backend server is running..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running${NC}"
else
    echo -e "${RED}✗ Backend server is NOT running${NC}"
    echo "Please start the server first:"
    echo "  cd /home/adhu/alefragnani.project-manager/medical-rag-qa"
    echo "  source /home/adhu/alefragnani.project-manager/.venv/bin/activate"
    echo "  uvicorn backend.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi
echo ""

# Check .env configuration
echo "2. Checking .env configuration..."
if [ -f ".env" ]; then
    LLM_BACKEND=$(grep "^LLM_BACKEND=" .env | cut -d'=' -f2)
    OLLAMA_MODEL=$(grep "^OLLAMA_MODEL=" .env | cut -d'=' -f2)
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo "  LLM_BACKEND: $LLM_BACKEND"
    echo "  OLLAMA_MODEL: $OLLAMA_MODEL"
else
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi
echo ""

# Check Ollama installation
echo "3. Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
    ollama --version
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama service is running${NC}"
        
        # Check if Meditron is pulled
        if ollama list | grep -q "meditron:7b"; then
            echo -e "${GREEN}✓ Meditron 7B model is installed${NC}"
        else
            echo -e "${YELLOW}⚠ Meditron 7B model not found${NC}"
            echo "  Install with: ollama pull meditron:7b"
        fi
    else
        echo -e "${YELLOW}⚠ Ollama service is not running${NC}"
        echo "  Start with: ollama serve (or systemctl start ollama)"
    fi
else
    echo -e "${YELLOW}⚠ Ollama is not installed${NC}"
    echo "  Install with: sudo snap install ollama"
    echo "  The system will use BioGPT fallback (functional)"
fi
echo ""

# Test query
echo "4. Testing system with sample query..."
echo "Query: 'What are the symptoms of diabetes?'"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  --data-binary '{"question":"What are the symptoms of diabetes?","mode":"auto"}')

# Extract key information
ANSWER=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['answer'][:200] + '...')" 2>/dev/null)
CONFIDENCE=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['confidence'])" 2>/dev/null)

if [ -n "$ANSWER" ]; then
    echo -e "${GREEN}✓ Query successful${NC}"
    echo ""
    echo "Answer Preview:"
    echo "$ANSWER"
    echo ""
    echo "Confidence: $CONFIDENCE"
    
    # Check for XML artifacts (BioGPT issue)
    if echo "$ANSWER" | grep -q "</FREETEXT>\|</ABSTRACT>\|▃"; then
        echo -e "${YELLOW}⚠ XML artifacts detected (using BioGPT fallback)${NC}"
        echo "  To fix: Install Ollama and Meditron (see QUICK_START_MEDITRON.md)"
    else
        echo -e "${GREEN}✓ Clean answer (no XML artifacts)${NC}"
    fi
else
    echo -e "${RED}✗ Query failed${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Summary
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo ""

if command -v ollama &> /dev/null && curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && ollama list | grep -q "meditron:7b"; then
    echo -e "${GREEN}✓ System Status: OPTIMAL (Using Meditron)${NC}"
    echo "  - Backend server: Running"
    echo "  - Ollama: Installed and running"
    echo "  - Meditron 7B: Installed"
    echo "  - Expected: Fast, clean answers without XML"
else
    echo -e "${YELLOW}⚠ System Status: FUNCTIONAL (Using BioGPT Fallback)${NC}"
    echo "  - Backend server: Running"
    echo "  - Ollama: Not fully configured"
    echo "  - Current LLM: BioGPT"
    echo "  - Expected: Answers with XML artifacts (functional but not optimal)"
    echo ""
    echo "To upgrade to Meditron:"
    echo "  1. sudo snap install ollama"
    echo "  2. ollama pull meditron:7b"
    echo "  3. Restart backend server"
    echo ""
    echo "See QUICK_START_MEDITRON.md for details"
fi
echo ""

echo "========================================="
echo "Documentation:"
echo "  - Quick Start: QUICK_START_MEDITRON.md"
echo "  - Setup Guide: OLLAMA_SETUP.md"
echo "  - Full Details: MEDITRON_INTEGRATION_COMPLETE.md"
echo "========================================="
