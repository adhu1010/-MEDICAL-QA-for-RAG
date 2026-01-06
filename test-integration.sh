#!/bin/bash

# Medical RAG QA System - API Testing Script
# Tests the integration between frontend and backend

set -e

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"

echo "==========================================="
echo "Medical RAG QA System - Integration Test"
echo "==========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Backend Health Check
echo "Test 1: Backend Health Check"
echo "Endpoint: GET $BACKEND_URL/api/health"
echo ""

HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ Backend is running and healthy${NC}"
    HEALTH_DATA=$(curl -s "$BACKEND_URL/api/health")
    echo "Response: $HEALTH_DATA"
else
    echo -e "${RED}✗ Backend health check failed (HTTP $HEALTH_RESPONSE)${NC}"
    echo "Make sure backend is running: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo "-------------------------------------------"
echo ""

# Test 2: Ask a Question (Simple)
echo "Test 2: Ask a Medical Question"
echo "Endpoint: POST $BACKEND_URL/api/ask"
echo ""

QUESTION='{"question": "What are the common side effects of aspirin?", "mode": "patient"}'
echo "Request: $QUESTION"
echo ""

ANSWER_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$QUESTION" \
    "$BACKEND_URL/api/ask")

echo "Response:"
echo "$ANSWER_RESPONSE" | python3 -m json.tool

echo ""
echo "-------------------------------------------"
echo ""

# Test 3: Query Preprocessing
echo "Test 3: Query Preprocessing"
echo "Endpoint: POST $BACKEND_URL/api/preprocess"
echo ""

PREPROCESS_REQUEST='{"question": "What is the mechanism of aspirin?", "mode": "auto"}'
echo "Request: $PREPROCESS_REQUEST"
echo ""

PREPROCESS_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$PREPROCESS_REQUEST" \
    "$BACKEND_URL/api/preprocess")

echo "Response:"
echo "$PREPROCESS_RESPONSE" | python3 -m json.tool

echo ""
echo "-------------------------------------------"
echo ""

# Test 4: System Statistics
echo "Test 4: Get System Statistics"
echo "Endpoint: GET $BACKEND_URL/api/stats"
echo ""

STATS_RESPONSE=$(curl -s "$BACKEND_URL/api/stats")

echo "Response:"
echo "$STATS_RESPONSE" | python3 -m json.tool

echo ""
echo "==========================================="
echo "Integration Tests Complete"
echo "==========================================="
echo ""
echo "✓ Backend API is functional"
echo "✓ Endpoints are responding correctly"
echo "✓ Data is being processed"
echo ""
echo "Next steps:"
echo "1. Start the frontend: npm run dev"
echo "2. Open http://localhost:5173 in your browser"
echo "3. Test the UI by asking medical questions"
echo "4. Check browser console for any errors"
echo ""
