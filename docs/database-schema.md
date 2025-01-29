# Database Schema

## MongoDB Collections

### hardware_configs
Stores system hardware configurations.
```javascript
{
  _id: ObjectId,
  cpu: {
    model: String,
    cores: Number,
    threads: Number,
    frequency: Number,
    microcode: String
  },
  gpu: [{
    model: String,
    driver: String,
    memory: Number
  }],
  ram: {
    total: Number,
    type: String,
    frequency: Number
  },
  storage: {
    type: String,
    size: Number
  },
  os: {
    name: String,
    version: String,
    kernel: String
  },
  bios: {
    vendor: String,
    version: String,
    date: Date
  },
  created_at: Date,
  updated_at: Date
}
```

### models
Stores information about discovered Ollama models.
```javascript
{
  _id: ObjectId,
  name: String,
  tags: [String],
  version: String,
  size: Number,
  modified: Date,
  created_at: Date,
  updated_at: Date
}
```

### test_sessions
Stores test session metadata and results.
```javascript
{
  _id: ObjectId,
  hardware_config_id: ObjectId,
  status: String,  // "running", "completed", "error"
  start_time: Date,
  end_time: Date,
  models: [{
    model_id: ObjectId,
    name: String,
    tests: [{
      type: String,  // "Test A", "Test B", "Test C"
      status: String,  // "running", "completed", "error"
      start_time: Date,
      end_time: Date,
      metrics: {
        inference_time: Number,
        tokens_per_second: Number,
        ram_usage: Number,
        vram_usage: Number,
        cpu_usage: Number,
        gpu_usage: Number
      },
      logs: [String]
    }]
  }],
  tags: [String],
  created_at: Date,
  updated_at: Date
}
```

### test_results
Stores detailed test results and metrics.
```javascript
{
  _id: ObjectId,
  session_id: ObjectId,
  model_id: ObjectId,
  test_type: String,
  metrics: {
    inference_time: Number,
    tokens_per_second: Number,
    ram_usage: [{
      timestamp: Date,
      value: Number
    }],
    vram_usage: [{
      timestamp: Date,
      value: Number
    }],
    cpu_usage: [{
      timestamp: Date,
      value: Number
    }],
    gpu_usage: [{
      timestamp: Date,
      value: Number
    }]
  },
  output: String,
  logs: [String],
  error: String,
  created_at: Date
}
```

## Indexes

### hardware_configs
```javascript
{
  "cpu.model": 1
}
{
  "gpu.model": 1
}
{
  "created_at": 1
}
```

### models
```javascript
{
  "name": 1
}
{
  "tags": 1
}
```

### test_sessions
```javascript
{
  "hardware_config_id": 1
}
{
  "start_time": 1
}
{
  "status": 1
}
{
  "tags": 1
}
```

### test_results
```javascript
{
  "session_id": 1
}
{
  "model_id": 1
}
{
  "test_type": 1
}
{
  "created_at": 1
}
```

## Relationships
- `test_sessions.hardware_config_id` → `hardware_configs._id`
- `test_sessions.models.model_id` → `models._id`
- `test_results.session_id` → `test_sessions._id`
- `test_results.model_id` → `models._id`
