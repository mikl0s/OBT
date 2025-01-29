# Technology Stack

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

## Architecture Decisions

### Why FastAPI?
- Excellent async support for concurrent test execution
- Built-in OpenAPI documentation
- Strong typing system for reliable API development
- Great performance for handling test data streams

### Why MongoDB?
- Flexible schema for varying hardware configurations
- Good performance for time-series test data
- Easy scaling if needed
- Rich query capabilities for dashboard features

### Why SvelteKit?
- Excellent performance
- Built-in SSR capabilities
- Small bundle size
- Great developer experience

### Why Podman?
- Daemonless container engine
- Rootless containers
- OCI compliance
- Better security model than Docker
