# OBT Tech Stack

## Frontend
- **Framework**: SvelteKit 2.0+
  - Fast, lightweight, and excellent DX
  - Built-in SSR capabilities
  - Real-time updates without page refreshes
- **UI Components**: 
  - Flowbite-Svelte for pre-built components
  - TailwindCSS for styling
  - Dark theme by default
  - Responsive design
  - Chart.js for visualizations
- **State Management**: 
  - Svelte stores for client state
  - Real-time model updates
  - Reactive search and filtering
- **Testing**: 
  - Playwright for E2E testing
  - Vitest for unit testing
  - c8 for coverage reporting
- **Code Quality**: 
  - ESLint with svelte plugin
  - Prettier for formatting
  - eslint-plugin-import for import order
  - pre-commit hooks for automation

## Backend
- **Framework**: FastAPI (0.100+) (Python)
  - High performance async server
  - Automatic OpenAPI documentation
  - Type-safe API endpoints
  - Real-time client tracking
- **Database**: 
  - SQLAlchemy ORM
  - SQLite for development
  - PostgreSQL for production
- **Testing**: 
  - pytest for unit tests
  - pytest-asyncio for async testing
  - pytest-cov for coverage
- **Code Quality**: 
  - Ruff for linting
  - Black for formatting
  - isort for import sorting
  - pre-commit hooks for automation
- **Client Management**: 
  - Async client registration
  - Heartbeat monitoring
  - Automatic cleanup of inactive clients
  - Cross-platform support

## Ollama Client
- **Core**: 
  - Python 3.10+
  - aiohttp for async HTTP
  - pydantic for data validation
- **Code Quality**: 
  - Same tools as backend
  - Shared pre-commit configuration

## Infrastructure
- **Development**: 
  - pnpm for package management
  - ESLint + Prettier for code formatting
  - Pre-commit hooks for quality control
  - Environment-based configuration
  - Docker for containerization
  - Docker Compose for orchestration
- **Monitoring**: 
  - Logging with Python's logging
  - Custom health check endpoints
  - Client heartbeat system

## External Integrations
- **Ollama API**: 
  - REST API for model management
  - Multi-client support
  - Cross-platform compatibility
  - Real-time model synchronization

## Hardware Detection
## Core Technologies

### Client Hardware Detection
- **Cross-Platform Support**
  - Windows, Linux, macOS supported
  - Platform-specific optimizations for each OS

### Hardware Detection Libraries
- **NVIDIA GPU Detection**
  - `pynvml`: NVIDIA Management Library for GPU info
  - Provides: VRAM, compute capability, driver versions
  - Tensor Core and FP16 support detection

- **AMD GPU Detection (Linux)**
  - `rocm-smi`: ROCm System Management Interface
  - Hardware info via command line tools
  - Memory and driver information

- **Apple Neural Engine (macOS)**
  - Native system tools: `sysctl`, `system_profiler`
  - M1/M2 chip detection and capabilities

- **Windows-Specific**
  - `wmi`: Windows Management Instrumentation
  - `pywin32`: Windows API access
  - `DirectML`: Intel/AMD NPU detection

- **Linux-Specific**
  - `lspci`: PCI device detection
  - Support for Movidius, Ryzen AI, Hexagon DSP

### System Information
- `psutil`: Cross-platform system monitoring
- `py-cpuinfo`: Detailed CPU information
- `distro`: Linux distribution detection

## Dependencies
- Core dependencies are cross-platform
- OS-specific dependencies are conditionally installed
- Optional components (e.g., DirectML) for enhanced detection

## Installation
- Windows: PowerShell installer script
- macOS/Linux: Manual installation via pip
- Virtual environment recommended for isolation

## Architecture Overview

### Components
1. **OBT Server (Port 8881)**
   - FastAPI backend server
   - Handles client registration and health tracking
   - Maintains client state and model information
   - Provides REST API for frontend

2. **Ollama Clients**
   - Python-based client service
   - Automatic registration with server
   - Regular heartbeat updates
   - Local model discovery and sync
   - Cross-platform support (Windows/Linux)

3. **Frontend (Port 5173)**
   - SvelteKit application
   - Modern dark-themed UI
   - Real-time updates
   - Advanced search and filtering
   - Multi-model selection

### Communication Flow
1. **Client Registration**
   - Clients auto-register with server on startup
   - Receive unique client ID
   - Begin heartbeat cycle

2. **Health Monitoring**
   - Regular heartbeat updates (10s default)
   - Automatic cleanup of inactive clients (60s timeout)
   - Real-time status updates to frontend

3. **Model Management**
   - Periodic model sync from clients
   - Real-time model updates to frontend
   - Support for model selection and operations
   - Search and filter capabilities

### Configuration
- **Backend**
  - Environment-based settings
  - Configurable timeouts and ports
  - Cross-origin support for development

- **Client**
  - Configurable server URL
  - Custom client ID support
  - Adjustable heartbeat interval
  - Local Ollama connection settings

- **Frontend**
  - Development proxy configuration
  - Environment-based API URLs
  - Real-time update settings

### Security Considerations
- All sensitive configuration via environment variables
- No hardcoded credentials
- Secure cross-origin policies
- Input validation on all endpoints
- Environment variables for secrets
- CORS configuration
- Rate limiting
- Input validation with Pydantic

### Performance
- Async I/O throughout
- Connection pooling
- Hardware-aware testing
- Benchmark result caching
