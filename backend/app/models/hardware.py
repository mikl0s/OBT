"""Hardware information models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    """Detailed CPU information."""

    name: str = Field(..., description="CPU model name")
    architecture: str = Field(..., description="CPU architecture (e.g., x86_64, arm64)")
    base_clock: float = Field(..., description="Base clock speed in GHz")
    boost_clock: Optional[float] = Field(
        None, description="Max boost clock speed in GHz"
    )
    cores: int = Field(..., description="Number of physical cores")
    threads: int = Field(..., description="Number of threads")
    core_types: Optional[Dict] = Field(
        None, description="Performance and efficiency core counts"
    )
    features: List[str] = Field(
        default_factory=list, description="AI-related CPU features (AVX-512, AMX, etc.)"
    )


class GPUInfo(BaseModel):
    """Detailed GPU information."""

    name: str = Field(..., description="GPU model name")
    vram_size: int = Field(..., description="VRAM size in MB")
    vram_type: str = Field(..., description="VRAM type (GDDR6X, HBM2, etc.)")
    tensor_cores: Optional[int] = Field(None, description="Number of tensor cores")
    cuda_cores: Optional[int] = Field(None, description="Number of CUDA cores")
    compute_capability: Optional[str] = Field(
        None, description="GPU compute capability version"
    )
    pcie_gen: Optional[int] = Field(None, description="PCIe generation")
    pcie_width: Optional[str] = Field(None, description="PCIe width (e.g., x16)")
    index: int = Field(..., description="GPU index in the system")


class RAMModule(BaseModel):
    """Information about a single RAM module."""

    size: int = Field(..., description="Module size in MB")
    speed: int = Field(..., description="Module speed in MHz")
    location: str = Field(..., description="Module location (e.g., DIMM_1)")
    type: str = Field(..., description="RAM type (e.g., DDR4)")


class RAMInfo(BaseModel):
    """Detailed RAM information."""

    speed: int = Field(..., description="Maximum RAM speed in MHz")
    type: str = Field(..., description="RAM type (e.g., DDR4)")
    channels: int = Field(..., description="Number of memory channels")
    modules: List[RAMModule] = Field(
        default_factory=list, description="List of RAM modules"
    )


class NPUInfo(BaseModel):
    """Neural Processing Unit information."""

    name: Optional[str] = Field(None, description="NPU name/model")
    compute_power: Optional[float] = Field(None, description="Compute power in TOPS")
    precision_support: Optional[List[str]] = Field(
        None, description="Supported precision formats"
    )
    dedicated: Optional[bool] = Field(None, description="Whether it's a dedicated NPU")


class FirmwareInfo(BaseModel):
    """System firmware and version information."""

    bios_version: str = Field(..., description="BIOS/UEFI version")
    bios_vendor: str = Field(..., description="BIOS/UEFI vendor")
    bios_release_date: str = Field(..., description="BIOS/UEFI release date")
    cpu_microcode: str = Field(..., description="CPU microcode version")
    os_name: str = Field(..., description="Operating system name")
    os_version: str = Field(..., description="Operating system version")
    os_kernel: str = Field(..., description="Operating system kernel version")
    ollama_version: str = Field(..., description="Ollama version")


class HardwareInfo(BaseModel):
    """Complete system hardware information."""

    cpu: CPUInfo = Field(..., description="CPU information")
    gpus: List[GPUInfo] = Field(default_factory=list, description="List of GPUs")
    ram: RAMInfo = Field(..., description="RAM information")
    npu: Optional[NPUInfo] = Field(None, description="NPU information if available")
    total_memory: int = Field(..., description="Total system memory in MB")
    firmware: FirmwareInfo = Field(..., description="System firmware and version info")


class ClientHardwareInfo(BaseModel):
    """Complete hardware information for a client."""

    id: str = Field(..., description="Client ID")
    version: str = Field(..., description="Client version")
    available: bool = Field(..., description="Whether client is available")
    last_heartbeat: str = Field(..., description="Last heartbeat timestamp")
    hardware: HardwareInfo = Field(..., description="Hardware information")
    models: List[Dict] = Field(default_factory=list, description="Available models")
