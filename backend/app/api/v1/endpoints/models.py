"""Models endpoints."""

import logging
from typing import Dict, List

from fastapi import APIRouter, Body, HTTPException, Query, WebSocket
from pydantic import BaseModel

from app.models.hardware import HardwareInfo
from app.models.ollama import OllamaModel
from app.services import ollama

logger = logging.getLogger(__name__)

router = APIRouter()


class HeartbeatRequest(BaseModel):
    """Heartbeat request body."""

    models: List[Dict]


class RegistrationRequest(BaseModel):
    """Registration request body."""

    hardware: HardwareInfo


class RegistrationResponse(BaseModel):
    """Registration response."""

    status: str
    registration_id: str


@router.post("/register", response_model=RegistrationResponse)
async def register_client(
    client_id: str = Query(..., description="Client identifier"),
    version: str = Query(..., description="Client version"),
    request: RegistrationRequest = Body(...),
):
    """Register an Ollama client."""
    registration_id = await ollama.register_client(client_id, version, request.hardware)
    return {"status": "success", "registration_id": registration_id}


@router.post("/sync")
async def sync_models(client_id: str, models: List[dict]):
    """Sync models from a client."""
    return await ollama.sync_models(client_id, models)


@router.post("/heartbeat")
async def client_heartbeat(
    client_id: str = Query(..., description="Client identifier"),
    version: str = Query(..., description="Client version"),
    available: bool = Query(..., description="Whether Ollama is available"),
    request: HeartbeatRequest = Body(None),
):
    """Update client heartbeat status."""
    try:
        models = request.models if request and request.models else []
        logger.info(f"Received heartbeat from {client_id} with {len(models)} models")
        success = await ollama.handle_heartbeat(client_id, version, available, models)
        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to update client status"
            )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error handling heartbeat from {client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=List[OllamaModel])
async def list_models(client_id: str = Query(..., description="Client identifier")):
    """List all installed models."""
    try:
        if not client_id:
            raise HTTPException(status_code=422, detail="client_id is required")

        if not await ollama.is_client_healthy(client_id):
            raise HTTPException(
                status_code=404, detail=f"Client {client_id} not found or not healthy"
            )

        models = await ollama.get_installed_models(client_id)
        if not models:
            logger.warning(f"No models found for client {client_id}")
        return models
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list models for client {client_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list models: {str(e)}"
        ) from e


@router.get("/clients")
async def list_clients():
    """List all healthy Ollama clients."""
    try:
        clients = await ollama.get_healthy_clients()
        if not clients:
            logger.warning("No healthy clients found")
        return clients
    except Exception as e:
        logger.error(f"Failed to list clients: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list clients: {str(e)}"
        ) from e


@router.websocket("/generate/{model_name}")
async def generate(websocket: WebSocket, model_name: str, client_id: str):
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
                websocket=websocket,
            )

    except Exception as e:
        await websocket.close(code=1001, reason=str(e))
