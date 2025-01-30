"""Ollama interaction service."""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

import aiohttp
from fastapi import HTTPException, WebSocket

from app.core.config import settings
from app.models.ollama import OllamaModel, OllamaResponse, TestType

# Store connected clients with their last heartbeat time and status
ollama_clients: Dict[str, Dict] = {}

# Client is considered unhealthy if no heartbeat in 60 seconds
CLIENT_TIMEOUT_SECONDS = 60

logger = logging.getLogger(__name__)

async def register_client(client_id: str, version: str):
    """Register an Ollama client."""
    ollama_clients[client_id] = {
        "version": version,
        "last_heartbeat": datetime.now(),
        "models": [],
        "available": False
    }

async def handle_heartbeat(client_id: str, version: str, ollama_available: bool, models: List[Dict]) -> bool:
    """Handle heartbeat from client."""
    if client_id not in ollama_clients:
        await register_client(client_id, version)
    
    client = ollama_clients[client_id]
    client["last_heartbeat"] = datetime.now()
    client["available"] = ollama_available
    client["version"] = version
    
    if ollama_available and models:
        client["models"] = await sync_models(client_id, models)
    else:
        client["models"] = []
    
    return True

def is_client_healthy(client_id: str) -> bool:
    """Check if client is healthy based on last heartbeat."""
    if client_id not in ollama_clients:
        return False
        
    client = ollama_clients[client_id]
    last_heartbeat = client["last_heartbeat"]
    time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
    
    return time_since_heartbeat < CLIENT_TIMEOUT_SECONDS and client["available"]

async def get_client(client_id: str) -> Optional[Dict]:
    """Get client info by ID."""
    if not is_client_healthy(client_id):
        return None
    return ollama_clients.get(client_id)

async def sync_models(client_id: str, models: List[Dict]) -> List[OllamaModel]:
    """Sync models from a client."""
    return [
        OllamaModel(
            name=model["name"],
            tags=model.get("tags", []),
            version=model.get("version", "unknown"),
            size=model.get("size", 0),
            modified=model.get("modified", 0)  # Store as timestamp
        )
        for model in models
    ]

async def get_installed_models(client_id: str) -> List[OllamaModel]:
    """Get list of installed Ollama models from a specific client."""
    client = await get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Ollama client {client_id} not found or not healthy"
        )
    return client["models"]

async def update_client_status(client_id: str, version: str, available: bool, models: List[dict]):
    """Update client status from heartbeat."""
    if client_id not in ollama_clients:
        logger.warning(f"Received heartbeat from unregistered client: {client_id}")
        return
        
    client = ollama_clients[client_id]
    client["version"] = version
    client["available"] = available
    client["last_heartbeat"] = datetime.now()
    client["models"] = models

async def generate_completion(
    client_id: str,
    model: str,
    prompt: str,
    websocket: WebSocket,
    stream: bool = True
) -> OllamaResponse:
    """Generate a completion from Ollama via client."""
    client = await get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Ollama client {client_id} not found or not healthy"
        )
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                f"{settings.OLLAMA_URL}/ws/generate/{model}"
            ) as ws:
                await ws.send_json({"prompt": prompt})
                
                full_response = ""
                reasoning = None
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            response = data.get("response", "")
                            done = data.get("done", False)
                            
                            if stream:
                                await websocket.send_json({
                                    "response": response,
                                    "done": done
                                })
                            
                            full_response += response
                            
                            if done:
                                break
                                
                        except json.JSONDecodeError:
                            continue
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
                
                if not stream:
                    await websocket.send_json({
                        "response": full_response,
                        "done": True
                    })
                
                return OllamaResponse(
                    response=full_response,
                    reasoning=reasoning
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate completion: {str(e)}"
        )

def get_healthy_clients() -> List[Dict[str, Any]]:
    """Get all healthy clients with their status."""
    healthy_clients = []
    for client_id, client in ollama_clients.items():
        if is_client_healthy(client_id):
            client_info = {
                "id": client_id,
                "version": client["version"],
                "available": client["available"],
                "model_count": len(client["models"]),
                "last_heartbeat": client["last_heartbeat"].isoformat()
            }
            healthy_clients.append(client_info)
    return healthy_clients

def cleanup_inactive_clients():
    """Remove clients that haven't sent a heartbeat in CLIENT_TIMEOUT_SECONDS."""
    current_time = datetime.now()
    to_remove = []
    
    for client_id, client in ollama_clients.items():
        time_since_heartbeat = (current_time - client["last_heartbeat"]).total_seconds()
        if time_since_heartbeat >= CLIENT_TIMEOUT_SECONDS:
            to_remove.append(client_id)
            
    for client_id in to_remove:
        logger.info(f"Removing inactive client: {client_id}")
        del ollama_clients[client_id]
        
    return to_remove
