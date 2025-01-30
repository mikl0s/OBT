"""Hardware information models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GPUInfo(BaseModel):
    """GPU information from client."""

    name: str = Field(..., description="GPU model name")
    memory: int = Field(..., description="GPU memory in MB")
    device_id: Optional[str] = Field(None, description="GPU device ID")


class HardwareInfo(BaseModel):
    """Hardware information from client."""

    cpu_threads: int = Field(..., description="Number of CPU threads")
    cpu_name: str = Field(..., description="CPU model name")
    total_memory: int = Field(..., description="Total system memory in MB")
    gpu_count: int = Field(0, description="Number of GPUs")
    gpu_name: Optional[str] = Field(None, description="Primary GPU name")
    gpu_memory: Optional[int] = Field(None, description="Primary GPU memory in MB")
    gpu_info: List[GPUInfo] = Field(
        default_factory=list, description="Detailed GPU information"
    )


class ClientHardwareInfo(BaseModel):
    """Complete hardware information for a client."""

    id: str = Field(..., description="Client ID")
    version: str = Field(..., description="Client version")
    available: bool = Field(..., description="Whether client is available")
    last_heartbeat: str = Field(..., description="Last heartbeat timestamp")
    hardware: HardwareInfo = Field(..., description="Hardware information")
    models: List[Dict] = Field(default_factory=list, description="Available models")
