# OBT Codebase Summary

## Key Components and Their Interactions

### Backend (`/backend`)
- **FastAPI Application**
  - `app/main.py`: Entry point, server configuration, and background tasks
  - `app/api/v1/endpoints/`: REST API endpoints
  - `app/services/`: Core business logic and client management
  - `app/models/`: Data models and schemas

### Ollama Client (`/ollama-client`)
- **Python Client Service**
  - `main.py`: Client service entry point
  - `models.py`: Data models for client-server communication
  - Installation scripts for Windows/Linux

### Frontend (`/frontend`)
- **SvelteKit Application**
  - `src/routes/`: Page components and routing
  - `src/lib/`: Shared components and utilities
  - `src/stores/`: State management
  - Dark-themed UI with Flowbite components

## Data Flow

### Client Registration Flow
1. Client starts up and reads configuration
2. Registers with server using unique client ID
3. Begins sending heartbeat signals every 10 seconds
4. Server monitors client health and removes inactive clients

### Model Management Flow
1. Client discovers local Ollama models
2. Sends model information with heartbeat
3. Server maintains current model state
4. Frontend fetches and displays models
5. Users can search, sort, and select models

## External Dependencies

### Backend Dependencies
```
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.0
python-dotenv==1.0.0
aiohttp==3.8.5
```

### Frontend Dependencies
```
@sveltejs/kit==1.20.4
flowbite-svelte==0.44.4
tailwindcss==3.3.3
```

### Client Dependencies
```
aiohttp==3.8.5
pydantic==2.0.0
python-dotenv==1.0.0
```

## Recent Significant Changes

### Multi-Client Support
- Added client registration system
- Implemented health monitoring
- Created client cleanup mechanism

### Model Management
- Added model discovery and sync
- Implemented model search and filtering
- Created multi-model selection interface

### UI Improvements
- Implemented dark theme
- Added responsive table layout
- Created search and filter interface
- Added model selection capabilities

## User Feedback Integration

### Implemented Features Based on Feedback
1. Added "None" option in client selection
2. Improved table layout for better readability
3. Added multi-model selection capability
4. Implemented real-time search filtering

### Pending Feedback Items
1. Performance testing capabilities
2. Model comparison features
3. Batch operations on selected models

## Development Guidelines

### Code Organization
- Backend follows FastAPI project structure
- Frontend uses SvelteKit file-based routing
- Shared types in dedicated type files
- Environment-based configuration

### State Management
- Client state managed by server
- Frontend uses Svelte stores
- Real-time updates via polling

### Testing Strategy
- Backend: Pytest for unit tests
- Frontend: Vitest for component testing
- E2E: Playwright for integration tests

### Development Workflow
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Create pull request

## Future Considerations

### Scalability
- Consider WebSocket for real-time updates
- Add caching for model information
- Implement batch operations

### Performance
- Add model operation queuing
- Implement request batching
- Add client-side caching

### Security
- Add authentication system
- Implement rate limiting
- Add request validation
