# OBT Ollama Client

This is a lightweight client that runs on the same machine as Ollama and communicates with the OBT server. It provides:

1. Model listing and synchronization with OBT
2. Hardware information reporting (CPU, GPU, memory, NPU)
3. Benchmark execution and performance monitoring
4. WebSocket-based streaming for model responses
5. Configurable connection to both Ollama and OBT server

## Features

### Hardware Detection
- Cross-platform support (Windows, Linux, macOS)
- Automatic detection of CPU and GPU resources:
  - NVIDIA GPUs with CUDA support
  - AMD GPUs with ROCm (Linux)
  - Apple Neural Engine (macOS)
  - Intel/AMD NPUs via DirectML (Windows)
  - Other NPUs (Intel Movidius, AMD Ryzen AI, etc.)
- Real-time hardware utilization tracking
- GPU/NPU capabilities:
  - Memory size and usage
  - Compute capabilities
  - Driver versions
  - Tensor Core support
  - FP16/BF16 support
- System memory and CPU usage reporting

### Benchmarking
- Local execution of model benchmarks
- Performance metrics collection:
  - Tokens per second
  - Latency measurements
  - Memory usage tracking
  - CPU/GPU utilization
- Multiple iteration support
- Automatic result reporting to OBT server

## Quick Start

### Windows
```powershell
# Download and run the installer (requires admin)
irm https://raw.githubusercontent.com/mikl0s/OBT/main/ollama-client/install.ps1 | iex
```

### macOS/Linux
```bash
# Clone the repository
git clone https://github.com/mikl0s/OBT.git
cd OBT/ollama-client

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
./venv/Scripts/activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OBT server URL
```

### Test Hardware Detection
To verify what hardware is detected on your system:
```bash
python show_hardware_info.py
```
This will display detailed information about your:
- CPU (model, cores, frequency)
- Memory (total, available)
- GPUs (NVIDIA, AMD)
- NPUs (Apple Neural Engine, Intel/AMD accelerators)
- System information

## Running

```bash
python main.py
```

The client will run on port 8002 by default. You can change this in the .env file.

## API Endpoints

### Model Management
- `GET /models` - List all installed Ollama models and sync with OBT

### Hardware Information
- `GET /hardware` - Get current hardware configuration and status

### Benchmarking
- `POST /benchmark/start` - Start a new benchmark
- `GET /benchmark/{id}` - Get benchmark status
- `GET /benchmark/{id}/metrics` - Get real-time benchmark metrics

### Streaming
- `WS /ws/generate/{model_name}` - WebSocket endpoint for streaming model responses

## Architecture

The client operates as a bridge between Ollama and the OBT server:

1. **Hardware Monitoring**
   - Collects hardware information from the local system
   - Reports status to OBT server via heartbeat messages

2. **Benchmarking**
   - Receives benchmark requests from OBT server
   - Executes benchmarks locally using Ollama
   - Collects performance metrics
   - Reports results back to OBT server

3. **Model Management**
   - Syncs installed models with OBT server
   - Manages model metadata and versions
