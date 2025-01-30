"""Ollama client that connects to OBT server."""

import asyncio
import json
import logging
import os
import signal
from datetime import datetime
from typing import Dict, List, Optional
import dateutil.parser

import aiohttp
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

__version__ = "0.1.0"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Starting Ollama Client v{__version__}")

# Global flag for graceful shutdown
shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received, cleaning up...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

class Settings(BaseSettings):
    """Application settings."""
    OBT_SERVER_URL: str = Field(default="http://localhost:8881")
    OLLAMA_URL: str = Field(default="http://localhost:11434")
    CLIENT_ID: str = Field(default="default-client")
    HEARTBEAT_INTERVAL: int = Field(default=10)  # seconds
    
    class Config:
        env_file = ".env"
        # Allow extra fields in .env to support legacy configs
        extra = "ignore"

settings = Settings()

class OllamaModel(BaseModel):
    """Ollama model information."""
    name: str
    tags: List[str] = []
    size: int = 0
    modified: float
    version: str = "unknown"

    class Config:
        json_encoders = {
            float: lambda v: v
        }

async def check_ollama_connection() -> bool:
    """Check if Ollama is available."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False

async def get_installed_models() -> List[OllamaModel]:
    """Get list of installed models from Ollama."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
            if response.status != 200:
                raise Exception(f"Failed to get models: {await response.text()}")
            data = await response.json()
            models = []
            for model in data.get("models", []):
                models.append(OllamaModel(
                    name=model["name"],
                    tags=model.get("tags", []),
                    size=model.get("size", 0),
                    modified=model.get("modified", 0),
                    version=model.get("version", "unknown")
                ))
            return models

async def register_with_server() -> bool:
    """Register this client with the OBT server."""
    try:
        logger.info(f"Registering with OBT server as {settings.CLIENT_ID} (version {__version__})")
        params = {
            "client_id": settings.CLIENT_ID,
            "version": __version__,
        }
        url = f"{settings.OBT_SERVER_URL}/api/v1/models/register"
        logger.debug(f"Registration URL: {url}?client_id={params['client_id']}&version={params['version']}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to register: {await response.text()}")
                    return False
                logger.info("Successfully registered with OBT server")
                return True
    except Exception as e:
        logger.error(f"Failed to register with server: {e}")
        return False

async def send_heartbeat() -> bool:
    """Send heartbeat to server with current status."""
    try:
        ollama_available = await check_ollama_connection()
        models = await get_installed_models() if ollama_available else []
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.OBT_SERVER_URL}/api/v1/models/heartbeat",
                params={
                    "client_id": settings.CLIENT_ID,
                    "version": __version__,
                    "available": str(ollama_available).lower(),  # Convert to string for query param
                },
                json={
                    "models": [model.model_dump() for model in models]  # Use model_dump() instead of dict()
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to send heartbeat: {await response.text()}")
                    return False
                return True
    except Exception as e:
        logger.error(f"Failed to send heartbeat: {e}")
        return False

async def heartbeat_loop():
    """Main heartbeat loop."""
    logger.info(f"Connecting to OBT server at {settings.OBT_SERVER_URL}")
    
    while not shutdown_event.is_set():
        if not await register_with_server():
            logger.error("Failed to register, retrying in 10 seconds...")
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=10)
            except asyncio.TimeoutError:
                continue
            continue

        while not shutdown_event.is_set():
            if not await send_heartbeat():
                break
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=settings.HEARTBEAT_INTERVAL)
            except asyncio.TimeoutError:
                continue
    
    logger.info("Heartbeat loop stopped")

async def main():
    """Main entry point."""
    try:
        await heartbeat_loop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down client...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled by signal handler
    logger.info("Client stopped")
