# OBT Codebase Summary

## Key Components and Their Interactions

### Backend (`/backend`)
- **FastAPI Application**
  - `app/main.py`: Entry point, server configuration, and background tasks
  - `app/api/v1/endpoints/`: REST API endpoints
  - `app/services/`: Core business logic and client management
  - `app/models/`: Data models and schemas
  - `app/benchmarks/`: Benchmarking functionality
    - `core/`: Core benchmarking engine
    - `schemas/`: Data models
    - `storage/`: Result storage
    - `tests/`: Unit tests

### Ollama Client (`/ollama-client`)
- **Python Client Service**
  - `main.py`: Client service entry point
  - `models.py`: Data models for client-server communication
  - Installation scripts for Windows/Linux
  - Configuration for client-server communication

### Frontend (`/frontend`)
- **SvelteKit Application**
  - `src/routes/`: Page components and routing
    - `benchmarks/`: New benchmarking UI components
    - `models/`: Model management interface
    - `tests/`: Test execution interface
  - `src/lib/`: Shared components and utilities
    - `stores/`: Svelte stores for state management
    - `types/`: TypeScript type definitions
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
sqlalchemy==1.4.42
```

### Frontend Dependencies
```
@sveltejs/kit==1.20.4
flowbite-svelte==0.44.4
tailwindcss==3.3.3
typescript==4.9.4
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

### Performance Testing Features
- Added comprehensive benchmarking suite
- Implemented hardware-aware testing (CPU/GPU)
- Added detailed performance metrics tracking
- Created benchmark comparison visualization

### Code Quality Improvements
- Added pre-commit hooks for consistent code quality
- Updated linting configurations:
  - ESLint and Prettier for frontend
  - Ruff, Black, and isort for backend
- Improved exception handling and error reporting
- Enhanced code organization and modularity

### UI Enhancements
- Added benchmark results visualization
- Implemented hardware configuration interface
- Enhanced model selection and comparison views

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
6. Code changes must pass pre-commit hooks:
   - Frontend: prettier → eslint-import → eslint → eslint-svelte
   - Backend: isort → black → ruff
7. All tests must pass before merging
8. Documentation must be updated for significant changes

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

## Codebase Summary

### Key Components

#### Backend (FastAPI)
- **API Endpoints**: REST API for client and model management
  - `/api/v1/models`: Client registration and model management
  - `/api/v1/hardware`: Hardware information tracking
  - `/api/v1/benchmarks`: Benchmark execution and results

- **Services**:
  - `ollama.py`: Client registration, heartbeat, and model sync
  - `hardware.py`: Hardware information collection and tracking
  - `benchmarks.py`: Benchmark execution and result management

- **Models**:
  - `hardware.py`: Hardware information data models
  - `ollama.py`: Client and model data structures
  - `benchmarks.py`: Benchmark configuration and results

#### Frontend (SvelteKit)
- **Pages**:
  - `/`: Dashboard overview
  - `/models`: Model management
  - `/tests`: Benchmark execution
  - `/benchmark`: Test results and analysis

- **Components**:
  - Hardware information display
  - Model selection interface
  - Test configuration forms
  - Result visualization

#### Ollama Client
- Hardware information collection
- Model status reporting
- Benchmark execution
- Registration session management

## Recent Changes

### v0.3.2
1. Client Registration Improvements
   - Added unique UUIDs for client registration sessions
   - Integrated hardware information collection
   - Added registration timestamp tracking

2. Hardware Information Management
   - Separated hardware info from heartbeat
   - Improved data model structure
   - Added hardware info storage

3. Test Session Tracking
   - Added registration ID to test results
   - Improved test session management
   - Enhanced result correlation

## Data Flow
1. Client registers with server (includes hardware info)
2. Server assigns registration UUID
3. Client maintains heartbeat with model status
4. Benchmark tests reference registration ID
5. Results stored with session context

## Dependencies
- FastAPI for backend API
- SvelteKit for frontend
- MongoDB for data storage
- Ollama for model execution

## Recent Significant Changes
- Implemented registration UUID system
- Enhanced hardware information tracking
- Improved test session management
- Updated documentation

## Next Steps
1. Test new registration system
2. Enhance result visualization
3. Implement batch operations
4. Add advanced analytics

## Codebase Summary

### Recent Changes

### Hardware Detection Enhancement (2025-01-31)
- Added comprehensive cross-platform hardware detection
- Extended NPU support for all major platforms:
  - Windows: NVIDIA CUDA, DirectML for Intel/AMD
  - Linux: NVIDIA, AMD ROCm, specialized NPUs
  - macOS: Apple Neural Engine on M1/M2
- Added detailed hardware capabilities reporting:
  - Memory size and utilization
  - Compute capabilities
  - Driver versions
  - Advanced features (Tensor Cores, FP16)

### Key Components

#### Hardware Information Module
- Location: `ollama-client/hardware_info.py`
- Purpose: Cross-platform hardware detection and monitoring
- Features:
  - CPU information and utilization
  - Memory status and management
  - GPU/NPU detection and capabilities
  - System information gathering
- Testing: Run `show_hardware_info.py` to verify detection

#### Client Installation
- Windows: PowerShell installer script
- macOS/Linux: Manual pip installation
- Environment setup and dependency management

## Data Flow
1. Hardware detection runs on client startup
2. Information gathered from multiple sources:
   - System APIs (psutil, cpuinfo)
   - GPU libraries (NVML, ROCm)
   - OS-specific tools (WMI, sysctl)
3. Data aggregated and normalized
4. Results reported to OBT server

## External Dependencies
See `requirements.txt` for full list
- Core libraries (cross-platform)
- OS-specific libraries (conditionally installed)
- Optional enhancements (DirectML, ROCm)
