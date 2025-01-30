# OBT Tech Stack

## Frontend
- **Framework**: SvelteKit
  - Fast, lightweight, and excellent DX
  - Built-in SSR capabilities
- **UI Components**: 
  - Flowbite-Svelte for pre-built components
  - TailwindCSS for styling
  - Dark theme by default
- **State Management**: 
  - Svelte stores
  - zod for runtime validation

## Backend
- **Framework**: FastAPI (Python)
  - High performance
  - Easy async support
  - Excellent type hints and validation
  - OpenAPI documentation out of the box
- **Database**: 
  - Primary: MongoDB (via motor for async support)
  - Secondary (if needed): libSQL
- **Testing**: 
  - Pytest for backend
  - Playwright for E2E
  - Vitest for frontend

## Infrastructure
- **Containerization**: 
  - Podman for MongoDB
  - Optional containers for backend/frontend
- **Development**: 
  - pnpm for package management
  - ESLint + Prettier for code formatting
  - Pre-commit hooks for quality control

## External Integrations
- **Ollama API**: 
  - REST API for model management
  - Local installation detection
  - Cross-platform support (Windows/Linux)

## Architecture Overview

### Components
1. **OBT Server (Port 8881)**
   - FastAPI backend server
   - Handles client registration and health tracking
   - Maintains client state and model information
   - Provides REST API for frontend

2. **Ollama Client**
   - Python-based client that connects to OBT server
   - Runs heartbeat loop every 10 seconds
   - Monitors local Ollama instance
   - Reports model status and availability
   - No HTTP server, uses active connection to OBT

3. **Frontend Dashboard**
   - SvelteKit web application
   - Connects only to OBT server
   - Displays model status and availability
   - Uses Flowbite components for UI

### Data Flow
1. Client → Server:
   - Registration request with client ID
   - Regular heartbeats with status
   - Model information updates

2. Server → Frontend:
   - Client health status
   - Available models
   - Error states and diagnostics

### Dependencies
- **Backend**:
  - FastAPI
  - MongoDB
  - Pydantic for validation
  - aiohttp for async HTTP

- **Client**:
  - aiohttp for async HTTP
  - Pydantic for settings
  - Python-dotenv for configuration

- **Frontend**:
  - SvelteKit
  - Flowbite-Svelte
  - Tailwind CSS

### Configuration
- Environment variables used throughout
- `.env.example` files provided for each component
- No hardcoded connection strings

### Security
- All sensitive data in environment variables
- Cross-origin protections in place
- Input validation on all endpoints

### Monitoring
- Client health tracked via heartbeats
- Connection status monitored
- Error logging in place

## Development Tools
- Git for version control
- pnpm for package management
- ESLint and Prettier for code formatting
