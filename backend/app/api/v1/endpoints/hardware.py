"""Hardware information endpoints."""

from typing import Dict, List

from fastapi import APIRouter, Body, HTTPException

from app.models.hardware import GPUInfo, HardwareInfo
from app.services.hardware import (
    get_available_gpus,
    get_system_info,
    update_client_hardware,
)

router = APIRouter()


@router.get("/", response_model=Dict[str, HardwareInfo])
async def get_hardware_info() -> Dict[str, HardwareInfo]:
    """Get hardware information from all active clients."""
    try:
        return await get_system_info()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve hardware information: {str(e)}",
        ) from e


@router.get("/gpu", response_model=List[GPUInfo])
async def get_gpu_info() -> List[GPUInfo]:
    """Get available GPU information from all clients."""
    try:
        return await get_available_gpus()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve GPU information: {str(e)}",
        ) from e


@router.post("/{client_id}")
async def update_hardware_info(client_id: str, hardware: HardwareInfo = Body(...)):
    """Update hardware information for a specific client."""
    try:
        await update_client_hardware(client_id, hardware)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update hardware information: {str(e)}",
        ) from e
