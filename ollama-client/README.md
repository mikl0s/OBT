# OBT Ollama Client

This is a lightweight client that runs on the same machine as Ollama and communicates with the OBT server. It provides:

1. Model listing and synchronization with OBT
2. WebSocket-based streaming for model responses
3. Configurable connection to both Ollama and OBT server

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your OBT server URL
```

## Running

```bash
python main.py
```

The client will run on port 8002 by default. You can change this in the .env file.

## API Endpoints

- `GET /models` - List all installed Ollama models and sync with OBT
- `WS /ws/generate/{model_name}` - WebSocket endpoint for streaming model responses
