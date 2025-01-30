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

echo -e "${BLUE}Starting OBT Services...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Clean up MongoDB
cleanup_mongodb

# Check if port 5173 is in use
if lsof -i :5173 > /dev/null 2>&1; then
    echo -e "${RED}Port 5173 is already in use. Please stop any running frontend server first.${NC}"
    exit 1
fi

# Check if port 8881 is in use
if lsof -i :8881 > /dev/null 2>&1; then
    echo -e "${RED}Port 8881 is already in use. Please stop any running backend server first.${NC}"
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
    docker logs obt-mongodb
    exit 1
fi

# Wait for MongoDB to be ready
echo -e "${BLUE}Waiting for MongoDB to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while ! docker exec obt-mongodb mongosh --quiet --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; do
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo -e "${BLUE}Still waiting for MongoDB (attempt $RETRY_COUNT/$MAX_RETRIES)...${NC}"
        docker logs --tail 5 obt-mongodb
    fi
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}MongoDB failed to start after $MAX_RETRIES seconds${NC}"
        echo -e "${RED}Last few lines of MongoDB logs:${NC}"
        docker logs --tail 20 obt-mongodb
        docker stop obt-mongodb
        docker rm obt-mongodb
        exit 1
    fi
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

uvicorn app.main:app --reload --host 0.0.0.0 --port 8881 &
BACKEND_PID=$!

# Start frontend
echo -e "${BLUE}Starting dashboard frontend...${NC}"
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
    echo -e "${GREEN}Services stopped${NC}"
}

trap cleanup EXIT

# Keep script running and show status
echo -e "${GREEN}All services are running!${NC}"
echo -e "${BLUE}Dashboard: ${GREEN}http://localhost:5173${NC}"
echo -e "${BLUE}Backend:   ${GREEN}http://localhost:8881${NC}"
echo -e "${BLUE}API Docs:  ${GREEN}http://localhost:8881/api/v1/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for user interrupt
wait
