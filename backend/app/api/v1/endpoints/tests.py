"""Test execution and management endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, WebSocket

from app.models.ollama import TestSession
from app.services.test_runner import start_test_session

router = APIRouter()


@router.post("/", response_model=TestSession)
async def create_test_session(model_names: List[str]) -> TestSession:
    """Create and start a new test session."""
    try:
        return await start_test_session(model_names)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start test session: {str(e)}",
        )


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
