# API Specification

## Base URL
- Development: `http://localhost:8000/api/v1`
- Production: Configurable via environment

## Endpoints

### Models

#### GET /models
Lists all discovered Ollama models.

```typescript
Response {
  models: Array<{
    name: string;
    tags: string[];
    version: string;
    size: number;
    modified: string;
  }>;
}
```

### Hardware Information

#### GET /hardware
Retrieves current system hardware information.

```typescript
Response {
  cpu: {
    model: string;
    cores: number;
    threads: number;
    frequency: number;
    microcode: string;
  };
  gpu: Array<{
    model: string;
    driver: string;
    memory: number;
  }>;
  ram: {
    total: number;
    type: string;
    frequency: number;
  };
  storage: {
    type: string;
    size: number;
  };
  os: {
    name: string;
    version: string;
    kernel: string;
  };
  bios: {
    vendor: string;
    version: string;
    date: string;
  };
}
```

### Test Sessions

#### POST /test-sessions
Create a new test session.

```typescript
Request {
  models: string[];  // List of model names to test
  testTypes: string[];  // List of test types to run
}

Response {
  sessionId: string;
  status: "started" | "error";
  message?: string;
}
```

#### GET /test-sessions
List test sessions with optional filters.

```typescript
Query {
  search?: string;
  tags?: string[];
  page?: number;
  limit?: number;
}

Response {
  sessions: Array<{
    id: string;
    date: string;
    models: string[];
    hardware: HardwareInfo;
    status: "running" | "completed" | "error";
    results?: TestResults[];
  }>;
  total: number;
  page: number;
  limit: number;
}
```

#### GET /test-sessions/{sessionId}
Get detailed information about a specific test session.

```typescript
Response {
  id: string;
  date: string;
  hardware: HardwareInfo;
  models: Array<{
    name: string;
    tests: Array<{
      type: string;
      status: "running" | "completed" | "error";
      metrics: {
        inferenceTime: number;
        tokensPerSecond: number;
        ramUsage: number;
        vramUsage: number;
        cpuUsage: number;
        gpuUsage: number;
      };
      logs: string[];
    }>;
  }>;
}
```

### Test Results

#### GET /test-results
Query test results with filters.

```typescript
Query {
  modelName?: string;
  hardwareConfig?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
}

Response {
  results: Array<{
    sessionId: string;
    modelName: string;
    hardware: HardwareInfo;
    metrics: TestMetrics;
    date: string;
  }>;
}
```

## WebSocket Endpoints

### /ws/test-progress
Real-time updates for test progress.

```typescript
Message {
  type: "progress" | "complete" | "error";
  sessionId: string;
  modelName: string;
  testType: string;
  progress: number;
  metrics?: TestMetrics;
  error?: string;
}
```

## Error Responses
All endpoints use standard HTTP status codes and return:

```typescript
Error {
  status: number;
  message: string;
  details?: any;
}
```

## Authentication
- Development: None required
- Production: API key via `X-API-Key` header (configurable)
