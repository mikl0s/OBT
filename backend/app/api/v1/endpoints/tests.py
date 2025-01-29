"""Test execution and management endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel

from app.models.ollama import TestSession
from app.services.prompts import get_available_prompts, get_prompt_content
from app.services.test_runner import start_test_session

router = APIRouter()


class TestRequest(BaseModel):
    """Test session request."""

    model_names: List[str]
    prompt_ids: Optional[List[str]] = None


@router.get("/prompts", response_model=List[dict])
async def list_prompts() -> List[dict]:
    """List all available test prompts."""
    return await get_available_prompts()


@router.post("/", response_model=TestSession)
async def create_test_session(request: TestRequest) -> TestSession:
    """Create and start a new test session."""
    try:
        # If no prompts specified, use all available prompts
        if not request.prompt_ids:
            prompts = await get_available_prompts()
            request.prompt_ids = [p["id"] for p in prompts]

        # Get prompt contents
        prompt_contents = await get_prompt_content(request.prompt_ids)
        return await start_test_session(request.model_names, prompt_contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start test session: {str(e)}",
        ) from e


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time test progress updates."""
    await websocket.accept()
    try:
        # TODO: Implement WebSocket handler for test progress
        pass
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
    finally:
        await websocket.close()
