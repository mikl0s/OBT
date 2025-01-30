"""Ollama client that connects to OBT server."""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    OBT_SERVER_URL: str = "http://localhost:8001"
    OLLAMA_URL: str = "http://localhost:11434"
    CLIENT_PORT: int = 8002
    
    class Config:
        env_file = ".env"

settings = Settings()
app = FastAPI(title="OBT Ollama Client")

class OllamaModel(BaseModel):
    """Ollama model information."""
    name: str
    tags: List[str] = []
    size: int = 0
    modified: datetime
    version: str = "unknown"

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp()
        }

class ModelResponse(BaseModel):
    """Response from model endpoint."""
    response: str
    done: bool
    reasoning: Optional[str] = None

async def forward_to_obt(endpoint: str, data: Dict) -> Dict:
    """Forward data to OBT server."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.OBT_SERVER_URL}/api/v1/{endpoint}",
            json=data
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Error from OBT server: {await response.text()}"
                )
            return await response.json()

@app.get("/models", response_model=List[OllamaModel])
async def list_models():
    """List all installed Ollama models."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch models from Ollama"
                    )
                data = await response.json()
                models = [
                    OllamaModel(
                        name=model["name"],
                        tags=model.get("tags", []),
                        version=model.get("version", "unknown"),
                        size=model.get("size", 0),
                        modified=datetime.fromtimestamp(model.get("modified", 0))
                    )
                    for model in data.get("models", [])
                ]
                
                # Forward to OBT server
                await forward_to_obt("models/sync", {
                    "models": [
                        {
                            "name": m.name,
                            "tags": m.tags,
                            "version": m.version,
                            "size": m.size,
                            "modified": m.modified.timestamp()
                        } for m in models
                    ]
                })
                return models
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )

@app.websocket("/ws/generate/{model_name}")
async def generate(websocket: WebSocket, model_name: str):
    """Generate completions and stream results back to OBT."""
    await websocket.accept()
    
    try:
        while True:
            # Receive prompt from OBT
            data = await websocket.receive_json()
            prompt = data.get("prompt")
            if not prompt:
                continue
                
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
                            # Forward to OBT
                            await websocket.send_json({
                                "response": result.get("response", ""),
                                "done": result.get("done", False)
                            })
                        except json.JSONDecodeError:
                            continue
                            
    except Exception as e:
        await websocket.close(code=1001, reason=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.CLIENT_PORT,
        reload=True
    )
