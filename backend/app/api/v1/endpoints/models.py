"""Models endpoints."""

from typing import List, Dict
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, WebSocket, Query, Body

from app.models.ollama import OllamaModel, OllamaResponse
from app.services import ollama

router = APIRouter()

class HeartbeatRequest(BaseModel):
    """Heartbeat request body."""
    models: List[Dict]

@router.post("/register")
async def register_client(
    client_id: str = Query(..., description="Client identifier"),
    version: str = Query(..., description="Client version")
):
    """Register an Ollama client."""
    await ollama.register_client(client_id, version)
    return {"status": "success"}

@router.post("/sync")
async def sync_models(client_id: str, models: List[dict]):
    """Sync models from a client."""
    return await ollama.sync_models(client_id, models)

@router.post("/heartbeat")
async def client_heartbeat(
    client_id: str = Query(..., description="Client identifier"),
    version: str = Query(..., description="Client version"),
    available: bool = Query(..., description="Whether Ollama is available"),
    request: HeartbeatRequest = Body(None)
):
    """Update client heartbeat status."""
    models = request.models if request else []
    await ollama.update_client_status(client_id, version, available, models)
    return {"status": "success"}

@router.get("/", response_model=List[OllamaModel])
async def list_models(client_id: str):
    """List all installed models."""
    try:
        return await ollama.get_installed_models(client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients")
async def list_clients():
    """List all healthy Ollama clients."""
    return ollama.get_healthy_clients()

@router.websocket("/generate/{model_name}")
async def generate(
    websocket: WebSocket,
    model_name: str,
    client_id: str
):
    """Generate completions from a model."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt")
            if not prompt:
                continue
                
            await ollama.generate_completion(
                client_id=client_id,
                model=model_name,
                prompt=prompt,
                websocket=websocket
            )
            
    except Exception as e:
        await websocket.close(code=1001, reason=str(e))
