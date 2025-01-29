"""Hardware information collection service."""

import platform
from typing import List

import cpuinfo
import psutil
from GPUtil import GPUtil

from app.models.hardware import BIOS, CPU, GPU, OS, RAM, HardwareConfig, Storage


async def get_system_info() -> HardwareConfig:
    """Collect system hardware information."""
    return HardwareConfig(
        cpu=await _get_cpu_info(),
        gpu=await _get_gpu_info(),
        ram=await _get_ram_info(),
        storage=await _get_storage_info(),
        os=await _get_os_info(),
        bios=await _get_bios_info(),
    )


async def _get_cpu_info() -> CPU:
    """Get CPU information."""
    info = cpuinfo.get_cpu_info()
    return CPU(
        model=info["brand_raw"],
        cores=psutil.cpu_count(logical=False),
        threads=psutil.cpu_count(logical=True),
        frequency=psutil.cpu_freq().current,
        microcode=info.get("microcode", "unknown"),
    )


async def _get_gpu_info() -> List[GPU]:
    """Get GPU information."""
    gpus = []
    try:
        for gpu in GPUtil.getGPUs():
            gpus.append(
                GPU(
                    model=gpu.name,
                    driver=gpu.driver,
                    memory=gpu.memoryTotal,
                )
            )
    except Exception:
        pass  # No GPU or unable to access GPU information
    return gpus


async def _get_ram_info() -> RAM:
    """Get RAM information."""
    mem = psutil.virtual_memory()
    return RAM(
        total=mem.total // (1024 * 1024),  # Convert to MB
        type="unknown",  # Need platform-specific method to get RAM type
        frequency=0,  # Need platform-specific method to get RAM frequency
    )


async def _get_storage_info() -> Storage:
    """Get storage information."""
    partitions = psutil.disk_partitions()
    # Get the root partition or first available
    for partition in partitions:
        if partition.mountpoint == "/" or partition.mountpoint == "C:\\":
            usage = psutil.disk_usage(partition.mountpoint)
            return Storage(
                type=partition.fstype,
                size=usage.total // (1024 * 1024 * 1024),  # Convert to GB
            )

    # Fallback to first partition if root not found
    if partitions:
        usage = psutil.disk_usage(partitions[0].mountpoint)
        return Storage(
            type=partitions[0].fstype,
            size=usage.total // (1024 * 1024 * 1024),
        )

    raise RuntimeError("No storage partitions found")


async def _get_os_info() -> OS:
    """Get operating system information."""
    return OS(
        name=platform.system(),
        version=platform.version(),
        kernel=platform.release(),
    )


async def _get_bios_info() -> BIOS:
    """Get BIOS information."""
    # This is platform-dependent and might require root access
    # Implement proper BIOS info collection based on OS
    return BIOS(
        vendor="unknown",
        version="unknown",
        date="unknown",
    )
