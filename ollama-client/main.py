"""Ollama client that connects to OBT server."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import dateutil.parser

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
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
    OBT_SERVER_URL: str = "http://localhost:8001/api/v1"
    OLLAMA_URL: str = "http://localhost:11434"
    CLIENT_PORT: int = 8002
    
    class Config:
        env_file = ".env"

settings = Settings()
app = FastAPI(title="OBT Ollama Client", version=__version__)

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

class ModelResponse(BaseModel):
    """Response from model endpoint."""
    response: str
    done: bool
    reasoning: Optional[str] = None

class VersionResponse(BaseModel):
    """Response from version endpoint."""
    version: str

@app.get("/version", response_model=VersionResponse)
async def get_version():
    """Get client version."""
    return VersionResponse(version=__version__)

async def forward_to_obt(endpoint: str, data: Dict) -> Dict:
    """Forward data to OBT server."""
    logger.debug(f"Forwarding to OBT endpoint {endpoint}")
    logger.debug(f"Data being sent: {json.dumps(data, default=str)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.OBT_SERVER_URL}/{endpoint}",
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error from OBT server: {error_text}")
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Error from OBT server: {error_text}"
                    )
                response_data = await response.json()
                logger.debug(f"Response from OBT: {json.dumps(response_data, default=str)}")
                return response_data
    except Exception as e:
        logger.error(f"Error forwarding to OBT: {str(e)}")
        raise

@app.get("/models", response_model=List[OllamaModel])
async def list_models():
    """List all installed Ollama models."""
    try:
        logger.info("Fetching models from Ollama")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
                if response.status != 200:
                    error_msg = f"Failed to fetch models from Ollama: {await response.text()}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=response.status,
                        detail=error_msg
                    )
                data = await response.json()
                logger.debug(f"Raw Ollama response: {json.dumps(data, default=str)}")
                
                models = []
                for model in data.get("models", []):
                    try:
                        # Parse the ISO timestamp to get Unix timestamp
                        modified_at = dateutil.parser.parse(model.get("modified_at", "1970-01-01T00:00:00Z"))
                        modified_timestamp = modified_at.timestamp()
                        
                        model_obj = OllamaModel(
                            name=model["name"],
                            tags=model.get("tags", []),
                            version=model.get("version", "unknown"),
                            size=model.get("size", 0),
                            modified=modified_timestamp
                        )
                        models.append(model_obj)
                    except Exception as e:
                        logger.error(f"Error creating model object: {str(e)}, model data: {json.dumps(model, default=str)}")
                        continue
                
                logger.debug(f"Created model objects: {[m.dict() for m in models]}")
                
                # Forward to OBT server
                try:
                    model_data = {
                        "models": [m.dict() for m in models]  # Use dict() instead of manual conversion
                    }
                    logger.debug(f"Forwarding model data: {json.dumps(model_data, default=str)}")
                    await forward_to_obt("models/sync", model_data)
                except Exception as e:
                    logger.error(f"Error forwarding to OBT: {str(e)}")
                    # Continue even if forwarding fails
                
                return models
    except Exception as e:
        error_msg = f"Failed to list models: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.websocket("/ws/generate/{model_name}")
async def generate(websocket: WebSocket, model_name: str):
    """Generate completions and stream results back to OBT."""
    logger.info(f"Established WebSocket connection for model {model_name}")
    await websocket.accept()
    
    try:
        while True:
            # Receive prompt from OBT
            data = await websocket.receive_json()
            prompt = data.get("prompt")
            if not prompt:
                continue
                
            logger.debug(f"Received prompt: {prompt}")
            
            # Stream to Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={"model": model_name, "prompt": prompt}
                ) as response:
                    async for line in response.content:
                        if not line:
                            continue
                        try:
                            result = json.loads(line)
                            logger.debug(f"Received result from Ollama: {json.dumps(result, default=str)}")
                            # Forward to OBT
                            await websocket.send_json({
                                "response": result.get("response", ""),
                                "done": result.get("done", False)
                            })
                        except json.JSONDecodeError:
                            logger.error("Error parsing result from Ollama")
                            continue
                            
    except Exception as e:
        logger.error(f"Error generating completions: {str(e)}")
        await websocket.close(code=1001, reason=str(e))

if __name__ == "__main__":
    logger.info("Starting Ollama client")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.CLIENT_PORT,
        reload=True
    )
