"""Ollama model management endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models.ollama import OllamaModel
from app.services.ollama import get_installed_models

router = APIRouter()


@router.get("/", response_model=List[OllamaModel])
async def list_models() -> List[OllamaModel]:
    """List all installed Ollama models."""
    try:
        return await get_installed_models()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model list: {str(e)}",
        )
