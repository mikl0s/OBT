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

# Function to download file from GitHub if it doesn't exist
download_github_file() {
    local filename="$1"
    local target_path="$2"
    
    if [ ! -f "$target_path" ]; then
        echo -e "${BLUE}Downloading $filename from GitHub...${NC}"
        local url="https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/$filename"
        if ! curl -fsSL "$url" -o "$target_path"; then
            echo -e "${RED}Error downloading $filename from GitHub${NC}"
            exit 1
        fi
        if [ ! -f "$target_path" ]; then
            echo -e "${RED}Failed to download $filename${NC}"
            exit 1
        fi
    fi
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -z "$SCRIPT_DIR" ]; then
    SCRIPT_DIR="$PWD"
fi

# Create directory if it doesn't exist
mkdir -p "$SCRIPT_DIR"

# Download required files if they don't exist
required_files=(".env.example" "requirements.txt" "start.sh" "main.py" "hardware_info.py" "show_hardware_info.py")
for file in "${required_files[@]}"; do
    download_github_file "$file" "$SCRIPT_DIR/$file"
done

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

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}Python version must be 3.8 or later. Current version: $PYTHON_VERSION${NC}"
    exit 1
fi

# Install Ollama if not present
echo -e "${BLUE}Checking Ollama installation...${NC}"
if ! command_exists ollama; then
    echo -e "${YELLOW}Ollama is not installed. Installing Ollama...${NC}"
    curl -fsSL https://ollama.ai/install.sh | sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Ollama${NC}"
        exit 1
    fi
fi

# Create virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# Create .env file if it doesn't exist
echo -e "${BLUE}Setting up .env file...${NC}"
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo -e "${YELLOW}Please edit .env file with your OBT server URL${NC}"
fi

# Make start script executable
chmod +x "$SCRIPT_DIR/start.sh"

# Create systemd service file
echo -e "${BLUE}Creating systemd service...${NC}"
cat > /etc/systemd/system/obt-ollama-client.service << EOL
[Unit]
Description=OBT Ollama Client
After=network.target ollama.service

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$SCRIPT_DIR/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}You can:${NC}"
echo -e "${YELLOW}1. Start the service: sudo systemctl start obt-ollama-client${NC}"
echo -e "${YELLOW}2. Enable service on boot: sudo systemctl enable obt-ollama-client${NC}"
echo -e "${YELLOW}3. Run manually: $SCRIPT_DIR/start.sh${NC}"
echo -e "${YELLOW}4. Edit .env file to configure the connection to OBT server${NC}"

# Ask to start the service
read -p "Would you like to start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start obt-ollama-client
    systemctl enable obt-ollama-client
    echo -e "${GREEN}Service started and enabled!${NC}"
fi
