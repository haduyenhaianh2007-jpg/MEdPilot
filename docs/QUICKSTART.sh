#!/bin/bash
# 🚀 MEDPILOT DEPLOYMENT - Quick Start Script

echo "=========================================="
echo "🏥 MedPilot Backend - Quick Start"
echo "=========================================="
echo""

# Color outputs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
check_ollama() {
    echo -e "${BLUE}Checking Ollama...${NC}"
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}❌ Ollama not found${NC}"
        echo "   Download from: https://ollama.ai"
        return 1
    fi
    echo -e "${GREEN}✅ Ollama installed${NC}"
    
    # Check if model exists
    if ollama list | grep -q "qwen2.5:7b"; then
        echo -e "${GREEN}✅ qwen2.5:7b model found${NC}"
    else
        echo -e "${YELLOW}⚠️  Model not found, pulling...${NC}"
        ollama pull qwen2.5:7b
    fi
}

check_python() {
    echo -e "${BLUE}Checking Python...${NC}"
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python not found${NC}"
        return 1
    fi
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
}

check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check required packages
    python -c "import fastapi; import pydantic; import requests; import chromadb; import sentence_transformers" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ All dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing dependencies, installing...${NC}"
        pip install -r requirements.txt
    fi
}

check_disease_data() {
    echo -e "${BLUE}Checking disease database...${NC}"
    if [ -f "app/database/data/diseases_data.json" ]; then
        SIZE=$(du -h "app/database/data/diseases_data.json" | cut -f1)
        echo -e "${GREEN}✅ diseases_data.json found (${SIZE})${NC}"
    else
        echo -e "${RED}❌ diseases_data.json not found${NC}"
        return 1
    fi
}

start_ollama() {
    echo ""
    echo -e "${YELLOW}Starting Ollama...${NC}"
    # Start Ollama in background
    ollama serve > ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo -e "${GREEN}✅ Ollama started (PID: $OLLAMA_PID)${NC}"
    
    # Wait for Ollama to be ready
    echo "   Waiting for Ollama to stabilize (30s)..."
    sleep 30
    
    # Verify Ollama is responding
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo -e "${GREEN}✅ Ollama responding on port 11434${NC}"
    else
        echo -e "${RED}❌ Ollama not responding${NC}"
        return 1
    fi
}

start_backend() {
    echo ""
    echo -e "${YELLOW}Starting Backend Server...${NC}"
    
    # Kill any existing process on port 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
    
    # Start backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    
    # Wait for backend to be ready
    echo "   Waiting for backend to start (5s)..."
    sleep 5
    
    # Verify backend is responding
    if curl -s http://localhost:8000/api/v1/ask-role > /dev/null; then
        echo -e "${GREEN}✅ Backend responding on port 8000${NC}"
    else
        echo -e "${RED}❌ Backend not responding${NC}"
        return 1
    fi
}

run_tests() {
    echo ""
    echo -e "${BLUE}Running tests...${NC}"
    echo "=========================================="
    
    python test/test_e2e.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests passed${NC}"
        echo "=========================================="
    else
        echo -e "${RED}❌ Tests failed${NC}"
        echo "=========================================="
        return 1
    fi
}

main() {
    # Prerequisites check
    echo -e "\n${BLUE}PHASE 1: Checking Prerequisites${NC}"
    echo "=========================================="
    check_ollama || return 1
    check_python || return 1
    check_dependencies || return 1
    check_disease_data || return 1
    
    # Start services
    echo -e "\n${BLUE}PHASE 2: Starting Services${NC}"
    echo "=========================================="
    start_ollama || return 1
    start_backend || return 1
    
    # Run tests
    echo -e "\n${BLUE}PHASE 3: Running Tests${NC}"
    run_tests || return 1
    
    # Success
    echo -e "\n${GREEN}=========================================="
    echo "🎉 MEDPILOT DEPLOYMENT SUCCESSFUL!"
    echo "=========================================="
    echo -e "${NC}"
    
    echo "📊 Services Running:"
    echo "   - Ollama:  http://localhost:11434"
    echo "   - Backend: http://localhost:8000"
    echo ""
    echo "🧪 Available Endpoints:"
    echo "   - GET  /api/v1/ask-role          (Role selection)"
    echo "   - POST /api/v1/query?role=doctor (Doctor mode)"
    echo "   - POST /api/v1/query?role=patient (Patient mode)"
    echo "   - POST /api/v1/chat              (Patient chat)"
    echo ""
    echo "📚 Documentation:"
    echo "   - IMPLEMENTATION_SUMMARY.md      (Full guide)"
    echo "   - test/README.md                 (Test guide)"
    echo ""
}

# Run main
main
