# Codebase Summary

## Project Structure

```
obt/
├── docs/                    # Project documentation
├── prompts/                 # Test prompts in markdown format
│   ├── writing500words.md  # Writing task prompt
│   ├── codingSudoko.md     # Coding task prompt
│   └── codingLandingpage.md # Web development prompt
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
└── pods/                  # Container configurations
    └── mongodb/           # MongoDB container setup
```

## Key Components

### Backend Components
1. **API Layer** (`backend/app/api/`)
   - REST endpoints for model management
   - Test execution endpoints
   - Results retrieval endpoints
   - `/api/v1/tests/prompts`: List available test prompts

2. **Core Services** (`backend/app/core/`)
   - Ollama integration
   - Hardware information collection
   - Test execution engine
   - Prompt management service

3. **Data Models** (`backend/app/models/`)
   - MongoDB schemas
   - Data validation models
   - Type definitions
   - `hardware.py`: System hardware configuration models
   - `ollama.py`: Ollama models and test result schemas
   - `base.py`: Base MongoDB model

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

### Ollama Integration Details
#### API Endpoints
- `/api/v1/hardware`: Hardware information collection
- `/api/v1/models`: Ollama model management
- `/api/v1/tests`: Test execution and monitoring
- `/api/v1/tests/prompts`: List available test prompts

#### Data Models
- `hardware.py`: System hardware configuration models
- `ollama.py`: Ollama models and test result schemas
- `base.py`: Base MongoDB model

#### Services
- `hardware.py`: Hardware information collection service
- `ollama.py`: Ollama API interaction service
- `test_runner.py`: Test execution service
- `prompts.py`: Prompt management service

### Test Prompts
The application uses markdown files in the `prompts/` directory for test scenarios:
1. `writing500words.md`: Tests model's ability to generate longer text
2. `codingSudoko.md`: Tests model's coding capabilities
3. `codingLandingpage.md`: Tests web development skills

Users can add or remove prompts by modifying markdown files in this directory. The system will automatically detect and use all `.md` files as test prompts.

### Data Flow
1. Hardware information is collected using system libraries (psutil, py-cpuinfo, GPUtil)
2. Ollama models are discovered through the Ollama API
3. Test prompts are loaded from the `prompts/` directory
4. Test sessions are created and run asynchronously
5. Test results, including reasoning and responses, are stored in MongoDB
6. Real-time updates are sent via WebSocket

### Recent Changes
- Initial project setup
- Documentation structure created
- Technology stack defined
- Added dynamic prompt loading from `prompts/` directory
   - Support for custom test prompts
   - Automatic prompt discovery
   - Optional prompt selection for tests
- Added Ollama response parsing with reasoning extraction
   - Captures content between `<think>` tags as reasoning
   - Separates reasoning from actual response
- Implemented test execution service
   - Supports completion and chat test types
   - Collects detailed metrics for each response
- Updated MongoDB schemas
   - Added reasoning field to response model
   - Enhanced test result structure

### External Dependencies
- MongoDB for data storage
- Local Ollama installation
- System hardware access
- FastAPI for API framework
- Motor for async MongoDB operations
- aiohttp for Ollama API communication
- psutil, py-cpuinfo, GPUtil for hardware metrics
