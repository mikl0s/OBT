"""Ollama client that connects to OBT server."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import dateutil.parser

import aiohttp
from pydantic import BaseModel
from pydantic_settings import BaseSettings

__version__ = "0.1.0"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Starting Ollama Client v{__version__}")

class Settings(BaseSettings):
    """Application settings."""
    OBT_SERVER_URL: str = "http://localhost:8881"
    OLLAMA_URL: str = "http://localhost:11434"
    CLIENT_ID: str = "default-client"
    HEARTBEAT_INTERVAL: int = 10  # seconds
    
    class Config:
        env_file = ".env"

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
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.OBT_SERVER_URL}/api/v1/models/register",
                json={
                    "client_id": settings.CLIENT_ID,
                    "version": __version__,
                }
            ) as response:
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
                json={
                    "client_id": settings.CLIENT_ID,
                    "version": __version__,
                    "ollama_available": ollama_available,
                    "models": [model.dict() for model in models]
                }
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed heartbeat: {await response.text()}")
                    return False
                logger.debug("Heartbeat successful")
                return True
    except Exception as e:
        logger.error(f"Failed to send heartbeat: {e}")
        return False

async def heartbeat_loop():
    """Main heartbeat loop."""
    while True:
        try:
            if not await register_with_server():
                logger.error("Failed to register, retrying in 10 seconds...")
            else:
                while True:
                    if not await send_heartbeat():
                        logger.error("Heartbeat failed, will retry registration")
                        break
                    await asyncio.sleep(settings.HEARTBEAT_INTERVAL)
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")
        await asyncio.sleep(settings.HEARTBEAT_INTERVAL)

async def main():
    """Main entry point."""
    logger.info(f"Connecting to OBT server at {settings.OBT_SERVER_URL}")
    await heartbeat_loop()

if __name__ == "__main__":
    asyncio.run(main())
