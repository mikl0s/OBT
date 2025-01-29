#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Store the root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check and cleanup MongoDB
cleanup_mongodb() {
    # Check for system MongoDB
    if pgrep mongod > /dev/null; then
        echo -e "${BLUE}Stopping system MongoDB...${NC}"
        sudo systemctl stop mongod 2>/dev/null || sudo service mongod stop 2>/dev/null
        sleep 2
    fi

    # Check for Docker MongoDB
    if docker ps | grep -q mongo; then
        echo -e "${BLUE}Stopping Docker MongoDB containers...${NC}"
        docker ps | grep mongo | awk '{print $1}' | xargs -r docker stop
        sleep 2
    fi

    # Remove our specific container if it exists
    if docker ps -a | grep -q obt-mongodb; then
        echo -e "${BLUE}Removing existing MongoDB container...${NC}"
        docker stop obt-mongodb 2>/dev/null
        docker rm obt-mongodb
    fi

    # Double check the port
    if lsof -i :27017 > /dev/null 2>&1; then
        echo -e "${RED}Port 27017 is still in use. Please check what's using it:${NC}"
        lsof -i :27017
        exit 1
    fi
}

# Function to check and setup Ollama
setup_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo -e "${BLUE}Installing Ollama...${NC}"
        curl -fsSL https://ollama.ai/install.sh | sh
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install Ollama${NC}"
            exit 1
        fi
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
        echo -e "${GREEN}Ollama is ready${NC}"
    else
        echo -e "${GREEN}Ollama is already running${NC}"
    fi
}

echo -e "${BLUE}Starting Ollama Benchmark Tool...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Clean up MongoDB
cleanup_mongodb

# Setup Ollama
setup_ollama

# Check if port 8001 is in use
if lsof -i :8001 > /dev/null 2>&1; then
    echo -e "${RED}Port 8001 is already in use. Please stop any running backend server first.${NC}"
    exit 1
fi

# Check if port 5173 is in use
if lsof -i :5173 > /dev/null 2>&1; then
    echo -e "${RED}Port 5173 is already in use. Please stop any running frontend server first.${NC}"
    exit 1
fi

# Start MongoDB container
echo -e "${BLUE}Creating MongoDB container...${NC}"
if ! docker run -d \
    --name obt-mongodb \
    -p 27017:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=obt_user \
    -e MONGO_INITDB_ROOT_PASSWORD=obt_password \
    -e MONGO_INITDB_DATABASE=obt_db \
    mongo:latest; then
    echo -e "${RED}Failed to start MongoDB container${NC}"
    exit 1
fi

# Wait for MongoDB to be ready
echo -e "${BLUE}Waiting for MongoDB to be ready...${NC}"
until docker exec obt-mongodb mongosh --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; do
    sleep 1
done
echo -e "${GREEN}MongoDB is ready${NC}"

# Start backend
echo -e "${BLUE}Starting backend server...${NC}"
cd "${ROOT_DIR}/backend" || exit 1
source venv/bin/activate

# Install python3-distutils if missing
if ! python3 -c "import distutils" 2>/dev/null; then
    echo -e "${BLUE}Installing python3-distutils...${NC}"
    sudo apt-get update && sudo apt-get install -y python3-distutils
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Start frontend
echo -e "${BLUE}Starting frontend server...${NC}"
cd "${ROOT_DIR}/frontend" || exit 1
pnpm run dev -- --host &
FRONTEND_PID=$!

# Handle cleanup on script exit
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    if docker ps | grep -q obt-mongodb; then
        echo -e "${BLUE}Stopping MongoDB container...${NC}"
        docker stop obt-mongodb
        docker rm obt-mongodb
    fi
    if [ ! -z "$OLLAMA_PID" ]; then
        echo -e "${BLUE}Stopping Ollama...${NC}"
        kill $OLLAMA_PID 2>/dev/null
    fi
    echo -e "${GREEN}Services stopped${NC}"
}

trap cleanup EXIT

# Keep script running and show status
echo -e "${GREEN}All services are running!${NC}"
echo -e "${BLUE}Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "${BLUE}Backend:  ${GREEN}http://localhost:8001${NC}"
echo -e "${BLUE}API Docs: ${GREEN}http://localhost:8001/api/v1/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for user interrupt
wait
