# Setup Guide

## Prerequisites

1. **Ollama**
   - Install Ollama on your system (Windows/Linux)
   - Verify installation: `ollama --version`

2. **Podman**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y podman podman-compose
   
   # Verify installation
   podman --version
   podman-compose --version
   ```

3. **Node.js and pnpm**
   ```bash
   # Install Node.js (v18+)
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install pnpm
   curl -fsSL https://get.pnpm.io/install.sh | sh -
   ```

4. **Python**
   ```bash
   # Install Python 3.10+
   sudo apt-get install -y python3.10 python3.10-venv
   ```

## MongoDB Setup with Podman

1. **Create a persistent volume**
   ```bash
   podman volume create mongodb_data
   ```

2. **Run MongoDB container**
   ```bash
   podman run -d \
     --name mongodb \
     -p 27017:27017 \
     -v mongodb_data:/data/db \
     -e MONGODB_INITDB_ROOT_USERNAME=admin \
     -e MONGODB_INITDB_ROOT_PASSWORD=secret \
     mongo:latest
   ```

3. **Verify MongoDB is running**
   ```bash
   podman ps
   ```

## Backend Setup

1. **Create Python virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB credentials
   ```

4. **Run backend**
   ```bash
   uvicorn app.main:app --reload
   ```

## Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   pnpm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your backend URL
   ```

3. **Run frontend**
   ```bash
   pnpm dev
   ```

## Development Setup

1. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

2. **Setup ESLint and Prettier**
   ```bash
   cd frontend
   pnpm install -D eslint prettier
   ```

## Testing

1. **Backend tests**
   ```bash
   cd backend
   pytest
   ```

2. **Frontend tests**
   ```bash
   cd frontend
   pnpm test
   ```

## Production Deployment

1. **Build frontend**
   ```bash
   cd frontend
   pnpm build
   ```

2. **Build backend**
   ```bash
   cd backend
   python -m build
   ```

3. **Deploy containers**
   ```bash
   cd pods
   podman-compose up -d
   ```

## Troubleshooting

### Common Issues

1. **MongoDB Connection**
   - Verify MongoDB is running: `podman ps`
   - Check logs: `podman logs mongodb`
   - Ensure credentials match in .env

2. **Ollama Detection**
   - Verify Ollama service: `ollama list`
   - Check permissions
   - Verify API endpoint is accessible

3. **Frontend Build**
   - Clear node_modules: `rm -rf node_modules`
   - Reinstall: `pnpm install`
   - Check for TypeScript errors

### Getting Help
- Check GitHub Issues
- Review logs in `logs/` directory
- Contact maintainers
