"""Hardware information collection module."""

import platform
import re
import subprocess
from typing import Dict, Optional

import cpuinfo
import psutil
import pynvml


def get_cpu_info() -> Dict:
    """Get detailed CPU information."""
    info = cpuinfo.get_cpu_info()
    cpu_freq = psutil.cpu_freq()

    # Get core types for hybrid architectures (e.g., Intel with P and E cores)
    core_types = None
    if platform.system() == "Windows":
        try:
            # Use wmic to get CPU info on Windows
            proc = subprocess.run(
                ["wmic", "cpu", "get", "Name,NumberOfCores,ThreadCount", "/format:csv"],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                lines = [
                    line.strip() for line in proc.stdout.split("\n") if line.strip()
                ]
                if len(lines) > 1:  # Skip header
                    _, name, cores, threads = lines[1].split(",")
                    if "Efficiency-cores" in name or "P-core" in name:
                        # Parse hybrid core info from name if available
                        p_cores = sum(1 for x in re.finditer(r"P-core", name))
                        e_cores = sum(1 for x in re.finditer(r"E-core", name))
                        if p_cores > 0 or e_cores > 0:
                            core_types = {
                                "performance_cores": p_cores or int(cores) // 2,
                                "efficiency_cores": e_cores or int(cores) // 2,
                            }
        except Exception:
            pass

    # Detect AI acceleration features
    features = []
    if info.get("flags"):
        ai_features = {
            "avx": ["avx"],
            "avx2": ["avx2"],
            "avx512": ["avx512f", "avx512_vnni"],
            "amx": ["amx_bf16", "amx_int8", "amx_tile"],
            "vnni": ["avx_vnni", "avx512_vnni"],
            "neon": ["neon"],  # ARM
            "sve": ["sve"],  # ARM Scalable Vector Extension
        }
        for feature, flags in ai_features.items():
            if any(
                flag.lower() in [f.lower() for f in info["flags"]] for flag in flags
            ):
                features.append(feature.upper())

    return {
        "name": info["brand_raw"],
        "architecture": info["arch"],
        "base_clock": (
            cpu_freq.current / 1000 if cpu_freq and cpu_freq.current else 0
        ),  # Convert MHz to GHz
        "boost_clock": (
            cpu_freq.max / 1000 if cpu_freq and cpu_freq.max else None
        ),  # Convert MHz to GHz
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "core_types": core_types,
        "features": features,
    }


def get_gpu_info() -> Optional[Dict]:
    """Get detailed GPU information."""
    try:
        # Try NVIDIA GPU first
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
            compute_cap = pynvml.nvmlDeviceGetCudaComputeCapability(handle)

            # Determine VRAM type based on GPU model
            vram_type = "GDDR6"
            if any(x in name for x in ["3090", "4090", "4080", "4070"]):
                vram_type = "GDDR6X"
            elif "A100" in name or "H100" in name:
                vram_type = "HBM2e"

            # Estimate CUDA cores based on compute capability and SM count
            attrs = pynvml.nvmlDeviceGetAttributes(handle)
            sm_count = attrs.multiprocessorCount
            cores_per_sm = {
                (8, 6): 128,  # Ampere
                (8, 9): 128,  # Ada Lovelace
                (9, 0): 128,  # Hopper
            }.get((compute_cap[0], compute_cap[1]), 64)

            cuda_cores = sm_count * cores_per_sm
            tensor_cores = (
                sm_count * 4
            )  # Most modern NVIDIA GPUs have 4 tensor cores per SM

            pynvml.nvmlShutdown()

            return {
                "name": name,
                "vram_size": info.total // (1024 * 1024),  # Convert to MB
                "vram_type": vram_type,
                "tensor_cores": tensor_cores,
                "cuda_cores": cuda_cores,
                "compute_capability": f"{compute_cap[0]}.{compute_cap[1]}",
            }
    except Exception:
        pass

    return None


def get_npu_info() -> Optional[Dict]:
    """Get NPU information if available."""
    # Check for Intel NPU
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "path", "win32_videocontroller", "get", "name", "/format:csv"],
                capture_output=True,
                text=True,
            )
            if "Intel Neural Compute" in result.stdout or "Intel VPU" in result.stdout:
                return {
                    "name": "Intel Neural Compute Engine",
                    "dedicated": True,
                    "precision_support": ["INT8", "FP16"],
                }
        else:
            result = subprocess.run(["lspci", "-v"], capture_output=True, text=True)
            if "Intel Neural Compute" in result.stdout:
                return {
                    "name": "Intel Neural Compute Engine",
                    "dedicated": True,
                    "precision_support": ["INT8", "FP16"],
                }
    except Exception:
        pass

    # Check for Apple Neural Engine
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return {
            "name": "Apple Neural Engine",
            "dedicated": True,
            "precision_support": ["INT8", "FP16"],
        }

    return None


def get_hardware_info() -> Dict:
    """Get complete hardware information."""
    return {
        "cpu": get_cpu_info(),
        "gpu": get_gpu_info(),
        "npu": get_npu_info(),
        "total_memory": psutil.virtual_memory().total // (1024 * 1024),  # Convert to MB
    }
