# Codebase Summary

## Project Structure

```
obt/
├── docs/                    # Project documentation
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── lib/           # Shared components
│   │   ├── routes/        # Page components
│   │   └── stores/        # State management
│   ├── static/            # Static assets
│   └── tests/             # Frontend tests
└── docker/                # Container configurations
    └── mongodb/           # MongoDB container setup
```

## Key Components

### Backend Components
1. **API Layer** (`backend/app/api/`)
   - REST endpoints for model management
   - Test execution endpoints
   - Results retrieval endpoints

2. **Core Services** (`backend/app/core/`)
   - Ollama integration
   - Hardware information collection
   - Test execution engine

3. **Data Models** (`backend/app/models/`)
   - MongoDB schemas
   - Data validation models
   - Type definitions

### Frontend Components
1. **Pages** (`frontend/src/routes/`)
   - Dashboard view
   - Model selection
   - Test results view

2. **Components** (`frontend/src/lib/`)
   - Reusable UI components
   - Data visualization
   - Form elements

3. **State Management** (`frontend/src/stores/`)
   - Test session state
   - UI state
   - Search/filter state

## Data Flow
1. User selects models for testing
2. Backend discovers local Ollama installation
3. Test execution engine runs benchmarks
4. Results stored in MongoDB
5. Frontend retrieves and displays results

## External Dependencies
- MongoDB for data storage
- Local Ollama installation
- System hardware access

## Recent Changes
- Initial project setup
- Documentation structure created
- Technology stack defined
