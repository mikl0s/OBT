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

    # Check for Podman MongoDB
    if podman ps | grep -q mongo; then
        echo -e "${BLUE}Stopping Podman MongoDB containers...${NC}"
        podman ps | grep mongo | awk '{print $1}' | xargs -r podman stop
        sleep 2
    fi

    # Remove our specific container if it exists
    if podman ps -a | grep -q obt-mongodb; then
        echo -e "${BLUE}Removing existing MongoDB container...${NC}"
        podman stop obt-mongodb 2>/dev/null
        podman rm obt-mongodb
    fi

    # Double check the port
    if lsof -i :27017 > /dev/null 2>&1; then
        echo -e "${RED}Port 27017 is still in use. Please check what's using it:${NC}"
        lsof -i :27017
        exit 1
    fi
}

echo -e "${BLUE}Starting OBT Services...${NC}"

# Check if Podman is available
if ! command -v podman >/dev/null 2>&1; then
    echo -e "${RED}Podman is not installed. Please install podman first.${NC}"
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
if ! podman run -d \
    --name obt-mongodb \
    -p 27017:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=obt_user \
    -e MONGO_INITDB_ROOT_PASSWORD=obt_password \
    -e MONGO_INITDB_DATABASE=obt_db \
    docker.io/library/mongo:latest; then
    echo -e "${RED}Failed to start MongoDB container${NC}"
    podman logs obt-mongodb || true
    exit 1
fi

# Wait for MongoDB to be ready
echo -e "${BLUE}Waiting for MongoDB to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while ! podman exec obt-mongodb mongosh --quiet --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; do
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo -e "${BLUE}Still waiting for MongoDB (attempt $RETRY_COUNT/$MAX_RETRIES)...${NC}"
        podman logs --tail 5 obt-mongodb
    fi
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}MongoDB failed to start after $MAX_RETRIES seconds${NC}"
        echo -e "${RED}Last few lines of MongoDB logs:${NC}"
        podman logs --tail 20 obt-mongodb
        podman stop obt-mongodb
        podman rm obt-mongodb
        exit 1
    fi
done
echo -e "${GREEN}MongoDB is ready${NC}"

# Start backend
echo -e "${BLUE}Starting backend server...${NC}"
cd "${ROOT_DIR}/backend" || exit 1

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Virtual environment not found. Please run setup.sh first.${NC}"
    cleanup_mongodb
    exit 1
fi

# Check if main.py exists
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}Backend main.py not found at app/main.py${NC}"
    cleanup_mongodb
    exit 1
fi

# Add backend directory to PYTHONPATH
export PYTHONPATH="${ROOT_DIR}/backend:${PYTHONPATH:-}"

# Start the backend server
cd "${ROOT_DIR}/backend" || exit 1
python3 -m app.main &
BACKEND_PID=$!

# Wait a moment to check if backend started successfully
sleep 2
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend server failed to start${NC}"
    cleanup_mongodb
    exit 1
fi

# Start frontend
echo -e "${BLUE}Starting frontend server...${NC}"
cd "${ROOT_DIR}/frontend" || exit 1
npm run dev &
FRONTEND_PID=$!

# Function to cleanup processes
cleanup() {
    echo -e "${BLUE}Cleaning up...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    cleanup_mongodb
}

trap cleanup EXIT

# Keep script running and show status
echo -e "${GREEN}All services are running!${NC}"
echo -e "Frontend: http://localhost:5173"
echo -e "Backend:  http://localhost:8881"
echo -e "MongoDB:  mongodb://localhost:27017"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for any process to exit
wait -n