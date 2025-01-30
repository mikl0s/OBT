# OBT Tech Stack

## Frontend
- **Framework**: SvelteKit
  - Fast, lightweight, and excellent DX
  - Built-in SSR capabilities
  - Real-time updates without page refreshes
- **UI Components**: 
  - Flowbite-Svelte for pre-built components
  - TailwindCSS for styling
  - Dark theme by default
  - Responsive design
- **State Management**: 
  - Svelte stores for client state
  - Real-time model updates
  - Reactive search and filtering

## Backend
- **Framework**: FastAPI (Python)
  - High performance async server
  - Automatic OpenAPI documentation
  - Type-safe API endpoints
  - Real-time client tracking
- **Client Management**: 
  - Async client registration
  - Heartbeat monitoring
  - Automatic cleanup of inactive clients
  - Cross-platform support
- **Testing**: 
  - Pytest for backend
  - Playwright for E2E
  - Vitest for frontend

## Infrastructure
- **Development**: 
  - pnpm for package management
  - ESLint + Prettier for code formatting
  - Pre-commit hooks for quality control
  - Environment-based configuration

## External Integrations
- **Ollama API**: 
  - REST API for model management
  - Multi-client support
  - Cross-platform compatibility
  - Real-time model synchronization

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
