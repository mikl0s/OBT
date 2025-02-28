"""Ollama interaction service."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import HTTPException, WebSocket

from app.core.config import settings
from app.models.hardware import HardwareInfo
from app.models.ollama import OllamaModel, OllamaResponse

# Store connected clients with their last heartbeat time and status
ollama_clients: Dict[str, Dict] = {}

# Client is considered unhealthy if 3 heartbeats are missed (15 seconds)
HEARTBEAT_INTERVAL_SECONDS = 5
MAX_MISSED_HEARTBEATS = 3
CLIENT_TIMEOUT_SECONDS = HEARTBEAT_INTERVAL_SECONDS * MAX_MISSED_HEARTBEATS

logger = logging.getLogger(__name__)


async def register_client(
    client_id: str, version: str, hardware: Optional[HardwareInfo] = None
):
    """Register an Ollama client."""
    registration_id = str(uuid.uuid4())
    ollama_clients[client_id] = {
        "version": version,
        "last_heartbeat": datetime.now(),
        "models": [],
        "available": False,
        "hardware": hardware.model_dump() if hardware else {},
        "registration_time": datetime.now(),
        "registration_id": registration_id,
        "missed_heartbeats": 0,
    }
    return registration_id


async def handle_heartbeat(
    client_id: str, version: str, ollama_available: bool, models: List[Dict]
) -> bool:
    """Handle heartbeat from client."""
    if client_id not in ollama_clients:
        # If client not found, register with new registration ID
        await register_client(client_id, version)

    await update_client_status(client_id, version, ollama_available, models)
    return True


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
            size=model.get("size", 0),
            modified=model.get("modified", 0),  # Store as timestamp
        )
        for model in models
    ]


async def get_installed_models(client_id: str) -> List[OllamaModel]:
    """Get list of installed Ollama models from a specific client."""
    client = await get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Ollama client {client_id} not found or not healthy",
        )
    return client["models"]


async def update_client_status(
    client_id: str, version: str, available: bool, models: List[dict]
):
    """Update client status from heartbeat."""
    if client_id not in ollama_clients:
        return

    # Convert models to OllamaModel instances
    ollama_models = [
        OllamaModel(
            name=model["name"],
            tags=model.get("tags", []),
            size=model.get("size", 0),
            modified=model.get("modified", 0),
        )
        for model in models
    ]

    ollama_clients[client_id].update(
        {
            "version": version,
            "last_heartbeat": datetime.now(),
            "available": available,
            "models": ollama_models,
            "missed_heartbeats": 0,
        }
    )


async def generate_completion(
    client_id: str, model: str, prompt: str, websocket: WebSocket, stream: bool = True
) -> OllamaResponse:
    """Generate a completion from Ollama via client."""
    client = await get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Ollama client {client_id} not found or not healthy",
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
                                await websocket.send_json(
                                    {"response": response, "done": done}
                                )

                            full_response += response

                            if done:
                                break

                        except json.JSONDecodeError:
                            continue
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break

                if not stream:
                    await websocket.send_json({"response": full_response, "done": True})

                return OllamaResponse(response=full_response, reasoning=reasoning)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate completion: {str(e)}"
        ) from e


async def is_client_healthy(client_id: str) -> bool:
    """Check if client is healthy based on last heartbeat."""
    try:
        if client_id not in ollama_clients:
            return False

        client = ollama_clients[client_id]
        if not client.get("available", False):
            return False

        last_heartbeat = client.get("last_heartbeat")
        if not last_heartbeat:
            return False

        time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
        missed_heartbeats = client.get("missed_heartbeats", 0)

        return (
            time_since_heartbeat < CLIENT_TIMEOUT_SECONDS
            and missed_heartbeats < MAX_MISSED_HEARTBEATS
        )
    except Exception as e:
        logger.error(f"Error checking client health for {client_id}: {e}")
        return False


async def get_healthy_clients() -> List[Dict[str, Any]]:
    """Get all healthy clients with their status."""
    try:
        healthy_clients = []
        current_time = datetime.now()

        for client_id, client in ollama_clients.items():
            if is_client_healthy(client_id):
                client_info = {
                    "id": client_id,
                    "version": client.get("version", "unknown"),
                    "available": client.get("available", False),
                    "model_count": len(client.get("models", [])),
                    "hardware": client.get("hardware", {}),
                    "last_heartbeat": (
                        current_time - client["last_heartbeat"]
                    ).total_seconds(),
                    "missed_heartbeats": client.get("missed_heartbeats", 0),
                }
                healthy_clients.append(client_info)

        return healthy_clients
    except Exception as e:
        logger.error(f"Error getting healthy clients: {e}")
        return []


async def get_active_clients() -> List[Dict[str, Any]]:
    """Get all active Ollama clients with their capabilities."""
    await cleanup_inactive_clients()

    active_clients = []
    for client_id, client in ollama_clients.items():
        if client["available"]:
            client_info = {
                "id": client_id,
                "version": client["version"],
                "available": True,
                "last_heartbeat": client["last_heartbeat"].isoformat(),
                "models": client["models"],
                "hardware": client.get("hardware", {}),
            }
            active_clients.append(client_info)

    return active_clients


async def cleanup_inactive_clients():
    """Remove clients that haven't sent a heartbeat in CLIENT_TIMEOUT_SECONDS."""
    current_time = datetime.now()
    to_remove = []

    for client_id, client in ollama_clients.items():
        time_since_heartbeat = (current_time - client["last_heartbeat"]).total_seconds()
        if time_since_heartbeat >= CLIENT_TIMEOUT_SECONDS:
            msg = (
                f"Client {client_id} has not sent heartbeat in "
                f"{time_since_heartbeat:.1f} seconds. Removing from active clients."
            )
            logger.warning(msg)
            to_remove.append(client_id)
        else:
            missed_heartbeats = int(time_since_heartbeat // HEARTBEAT_INTERVAL_SECONDS)
            client["missed_heartbeats"] = missed_heartbeats
            if missed_heartbeats > 0:
                remaining = MAX_MISSED_HEARTBEATS - missed_heartbeats
                msg = (
                    f"Client {client_id} has missed {missed_heartbeats} heartbeats. "
                    f"Will be removed after {remaining} more misses."
                )
                logger.info(msg)

    for client_id in to_remove:
        del ollama_clients[client_id]
