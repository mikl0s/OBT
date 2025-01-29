#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}Ollama is not installed. Please install it first:${NC}"
    echo -e "${BLUE}curl -fsSL https://ollama.ai/install.sh | sh${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${BLUE}Starting Ollama service...${NC}"
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready
    echo -e "${BLUE}Waiting for Ollama to be ready...${NC}"
    until curl -s http://localhost:11434/api/tags &> /dev/null; do
        sleep 1
    done
fi

# Start the client
echo -e "${BLUE}Starting OBT Ollama client...${NC}"
source venv/bin/activate
python main.py
