# Codebase Summary

## Project Structure

```
obt/
├── backend/                 # OBT Server
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── v1/             # API version 1
│   └── requirements.txt    # Python dependencies
├── ollama-client/          # Ollama Client
│   ├── main.py             # Main client logic
│   └── .env.example        # Configuration template
├── frontend/               # Frontend Dashboard
│   ├── src/
│   │   ├── lib/           # Shared components
│   │   ├── routes/        # Page components
│   │   └── stores/        # State management
│   ├── static/            # Static assets
│   └── tests/             # Frontend tests
└── pods/                  # Container configurations
    └── mongodb/           # MongoDB container setup
```

## Key Components

### OBT Server
- **Location**: `/backend/`
- **Purpose**: Central server that manages Ollama clients and provides API for frontend
- **Key Files**:
  - `app/services/ollama.py`: Client management and health tracking
  - `app/models/ollama.py`: Data models for client and model information
  - `app/api/v1/models.py`: API endpoints for model operations

### Ollama Client
- **Location**: `/ollama-client/`
- **Purpose**: Connects to local Ollama instance and reports status to OBT server
- **Key Files**:
  - `main.py`: Main client logic with heartbeat system
  - `.env.example`: Configuration template

### Frontend Dashboard
- **Location**: `/frontend/`
- **Purpose**: Web interface for monitoring Ollama clients and models
- **Key Files**:
  - `src/routes/models/+page.svelte`: Model list and status display
  - `src/routes/clients/+page.svelte`: Client health monitoring

## Data Flow

### Client Registration Flow
1. Client starts up and reads configuration
2. Attempts to register with OBT server
3. Begins sending regular heartbeats
4. Reports model information if Ollama is available

### Model Status Flow
1. Client checks Ollama connection
2. Fetches installed models if connected
3. Sends model list with heartbeat
4. Server updates stored model information
5. Frontend fetches latest status from server

## Recent Changes

### Architecture Updates
- Moved from HTTP server to heartbeat system for client
- Centralized client health tracking in OBT server
- Improved error handling and status reporting

### Client Changes
- Removed FastAPI server from client
- Added heartbeat loop with configurable interval
- Improved error handling and logging
- Updated configuration system

### Frontend Changes
- Updated to work with new server architecture
- Improved error messages and user guidance
- Added client health status display

## External Dependencies
- MongoDB for data storage
- Ollama for model hosting
- FastAPI for backend server
- SvelteKit for frontend

## Configuration
Each component has its own configuration:
- Backend: Environment variables for MongoDB and server settings
- Client: `.env` file for server URL and client settings
- Frontend: Build-time configuration for API endpoints
