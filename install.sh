#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root or with sudo${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command_exists python3; then
    echo -e "${RED}Python is not installed. Installing Python...${NC}"
    if command_exists apt-get; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv
    elif command_exists dnf; then
        dnf install -y python3 python3-pip python3-virtualenv
    elif command_exists yum; then
        yum install -y python3 python3-pip python3-virtualenv
    elif command_exists pacman; then
        pacman -Sy python python-pip
    else
        echo -e "${RED}Could not install Python. Please install Python 3.8 or later manually${NC}"
        exit 1
    fi
fi

# Check Node.js and pnpm
echo -e "${BLUE}Checking Node.js and pnpm...${NC}"
if ! command_exists node; then
    echo -e "${YELLOW}Node.js is not installed. Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
fi

if ! command_exists pnpm; then
    echo -e "${YELLOW}pnpm is not installed. Installing pnpm...${NC}"
    curl -fsSL https://get.pnpm.io/install.sh | sh -
    source /root/.bashrc
fi

# Check Docker
echo -e "${BLUE}Checking Docker installation...${NC}"
if ! command_exists docker; then
    echo -e "${YELLOW}Docker is not installed. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

# Create OBT directory
echo -e "${BLUE}Setting up OBT...${NC}"
INSTALL_DIR="/opt/obt"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone repository
echo -e "${BLUE}Cloning OBT repository...${NC}"
if [ ! -d ".git" ]; then
    git clone https://github.com/mikl0s/OBT.git .
fi

# Setup backend
echo -e "${BLUE}Setting up backend...${NC}"
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Setup frontend
echo -e "${BLUE}Setting up frontend...${NC}"
cd frontend
pnpm install
cd ..

# Make start script executable
chmod +x start.sh

# Create systemd service
echo -e "${BLUE}Creating systemd service...${NC}"
cat > /etc/systemd/system/obt.service << EOL
[Unit]
Description=Ollama Benchmark Tool
After=network.target docker.service

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}You can:${NC}"
echo -e "${YELLOW}1. Start the service: sudo systemctl start obt${NC}"
echo -e "${YELLOW}2. Enable service on boot: sudo systemctl enable obt${NC}"
echo -e "${YELLOW}3. Run manually: cd $INSTALL_DIR && ./start.sh${NC}"

# Ask to start the service
read -p "Would you like to start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start obt
    systemctl enable obt
    echo -e "${GREEN}Service started and enabled!${NC}"
    echo -e "${GREEN}OBT is now available at:${NC}"
    echo -e "${BLUE}Frontend: ${GREEN}http://localhost:5173${NC}"
    echo -e "${BLUE}Backend:  ${GREEN}http://localhost:8001${NC}"
    echo -e "${BLUE}API Docs: ${GREEN}http://localhost:8001/api/v1/docs${NC}"
fi
