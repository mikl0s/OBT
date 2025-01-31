"""Hardware information collection module."""

import platform
import re
import subprocess
from typing import Dict, Optional

import cpuinfo
import psutil
import torch


def get_cpu_info() -> Dict:
    """Get detailed CPU information."""
    info = cpuinfo.get_cpu_info()
    cpu_freq = psutil.cpu_freq()

    # Get core types for hybrid architectures (e.g., Intel with P and E cores)
    core_types = None
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo_text = f.read()
                # Look for core type identifiers (specific to different CPU architectures)
                p_cores = len(
                    re.findall(
                        r"processor.*\n.*cpu cores.*\n.*power", cpuinfo_text, re.M
                    )
                )
                e_cores = len(
                    re.findall(
                        r"processor.*\n.*cpu cores.*\n.*efficient", cpuinfo_text, re.M
                    )
                )
                if p_cores > 0 or e_cores > 0:
                    core_types = {
                        "performance_cores": p_cores,
                        "efficiency_cores": e_cores,
                    }
        except Exception:
            pass

    # Detect AI acceleration features
    features = []
    if info.get("flags"):
        ai_features = {
            "avx512": ["avx512f", "avx512_vnni"],
            "amx": ["amx_bf16", "amx_int8", "amx_tile"],
            "vnni": ["avx_vnni", "avx512_vnni"],
            "neon": ["neon"],  # ARM
            "sve": ["sve"],  # ARM Scalable Vector Extension
        }
        for feature, flags in ai_features.items():
            if any(flag in info["flags"] for flag in flags):
                features.append(feature.upper())

    return {
        "name": info["brand_raw"],
        "architecture": info["arch"],
        "base_clock": cpu_freq.current / 1000,  # Convert MHz to GHz
        "boost_clock": cpu_freq.max / 1000 if cpu_freq.max else None,
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "core_types": core_types,
        "features": features,
    }


def get_gpu_info() -> Optional[Dict]:
    """Get detailed GPU information."""
    if not torch.cuda.is_available():
        return None

    try:
        gpu_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)

        # Determine VRAM type based on GPU model
        vram_type = (
            "GDDR6X"
            if any(x in gpu_name for x in ["3090", "4090", "4080"])
            else "GDDR6"
        )
        if "A100" in gpu_name or "H100" in gpu_name:
            vram_type = "HBM2e"

        return {
            "name": gpu_name,
            "vram_size": props.total_memory // (1024 * 1024),  # Convert to MB
            "vram_type": vram_type,
            "tensor_cores": props.max_compute_units,  # This is approximate
            "cuda_cores": props.max_compute_units * 64,  # Approximate based on SM count
            "compute_capability": f"{props.major}.{props.minor}",
        }
    except Exception:
        return None


def get_npu_info() -> Optional[Dict]:
    """Get NPU information if available."""
    # Check for Intel NPU
    try:
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
