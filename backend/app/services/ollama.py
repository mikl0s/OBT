"""Ollama interaction service."""

import json
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from fastapi import HTTPException, WebSocket

from app.core.config import settings
from app.models.ollama import OllamaModel, OllamaResponse, TestType

# Store connected clients
ollama_clients: Dict[str, str] = {}

async def register_client(client_url: str, client_id: str):
    """Register an Ollama client."""
    ollama_clients[client_id] = client_url

async def get_client(client_id: str) -> Optional[str]:
    """Get client URL by ID."""
    return ollama_clients.get(client_id)

async def sync_models(client_id: str, models: List[Dict]) -> List[OllamaModel]:
    """Sync models from a client."""
    return [
        OllamaModel(
            name=model["name"],
            tags=model.get("tags", []),
            version=model.get("version", "unknown"),
            size=model.get("size", 0),
            modified=datetime.fromtimestamp(model.get("modified", 0))
        )
        for model in models
    ]

async def get_installed_models(client_id: str) -> List[OllamaModel]:
    """Get list of installed Ollama models from a specific client."""
    client_url = await get_client(client_id)
    if not client_url:
        raise HTTPException(
            status_code=404,
            detail=f"Ollama client {client_id} not found"
        )
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{client_url}/models") as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch models from Ollama client"
                    )
                data = await response.json()
                return [
                    OllamaModel(
                        name=model["name"],
                        tags=model.get("tags", []),
                        version=model.get("version", "unknown"),
                        size=model.get("size", 0),
                        modified=datetime.fromtimestamp(model.get("modified", 0))
                    )
                    for model in data
                ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )

async def generate_completion(
    client_id: str,
    model: str,
    prompt: str,
    websocket: WebSocket,
    stream: bool = True
) -> OllamaResponse:
    """Generate a completion from Ollama via client."""
    client_url = await get_client(client_id)
    if not client_url:
        raise HTTPException(
            status_code=404,
            detail=f"Ollama client {client_id} not found"
        )
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                f"{client_url}/ws/generate/{model}"
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
