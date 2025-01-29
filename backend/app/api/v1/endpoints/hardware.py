"""Hardware information endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models.hardware import HardwareConfig
from app.services.hardware import get_system_info

router = APIRouter()


@router.get("/", response_model=HardwareConfig)
async def get_hardware_info() -> HardwareConfig:
    """Get current system hardware information."""
    try:
        return await get_system_info()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve hardware information: {str(e)}",
        )
