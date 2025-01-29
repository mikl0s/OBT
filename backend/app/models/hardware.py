"""Hardware information models."""

from typing import List, Optional

from pydantic import Field

from app.models.base import MongoModel


class CPU(MongoModel):
    """CPU information model."""

    model: str = Field(..., description="CPU model name")
    cores: int = Field(..., description="Number of physical cores")
    threads: int = Field(..., description="Number of threads")
    frequency: float = Field(..., description="Base frequency in MHz")
    microcode: str = Field(..., description="CPU microcode version")


class GPU(MongoModel):
    """GPU information model."""

    model: str = Field(..., description="GPU model name")
    driver: str = Field(..., description="GPU driver version")
    memory: int = Field(..., description="GPU memory in MB")


class RAM(MongoModel):
    """RAM information model."""

    total: int = Field(..., description="Total RAM in MB")
    type: str = Field(..., description="RAM type (e.g., DDR4)")
    frequency: int = Field(..., description="RAM frequency in MHz")


class Storage(MongoModel):
    """Storage information model."""

    type: str = Field(..., description="Storage type (e.g., SSD, NVMe)")
    size: int = Field(..., description="Storage size in GB")


class OS(MongoModel):
    """Operating system information model."""

    name: str = Field(..., description="OS name")
    version: str = Field(..., description="OS version")
    kernel: str = Field(..., description="Kernel version")


class BIOS(MongoModel):
    """BIOS information model."""

    vendor: str = Field(..., description="BIOS vendor")
    version: str = Field(..., description="BIOS version")
    date: str = Field(..., description="BIOS date")


class HardwareConfig(MongoModel):
    """Complete hardware configuration model."""

    cpu: CPU = Field(..., description="CPU information")
    gpu: List[GPU] = Field(default_factory=list, description="List of GPUs")
    ram: RAM = Field(..., description="RAM information")
    storage: Storage = Field(..., description="Storage information")
    os: OS = Field(..., description="OS information")
    bios: BIOS = Field(..., description="BIOS information")
    tags: List[str] = Field(default_factory=list, description="Hardware configuration tags")
