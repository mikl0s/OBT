"""Hardware information collection module."""

import platform
import re
import subprocess
from typing import Dict, List, Optional

import cpuinfo
import distro
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


def get_ram_info() -> Dict:
    """Get detailed RAM information."""
    ram = psutil.virtual_memory()
    info = {
        "total": ram.total // (1024 * 1024),  # Convert to MB
        "speed": 0,
        "type": "Unknown",
        "channels": 1,
    }

    try:
        if platform.system() == "Windows":
            # Use wmic to get RAM info on Windows
            proc = subprocess.run(
                [
                    "wmic",
                    "memorychip",
                    "get",
                    "Speed,MemoryType,DeviceLocator,Capacity",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                lines = [
                    line.strip() for line in proc.stdout.split("\n") if line.strip()
                ]
                if len(lines) > 1:  # Skip header
                    channels = set()
                    max_speed = 0
                    for line in lines[1:]:
                        if not line:
                            continue
                        try:
                            parts = line.split(",")
                            if len(parts) >= 4:  # Node,Speed,Type,Location,Capacity
                                speed = int(parts[1]) if parts[1].isdigit() else 0
                                max_speed = max(max_speed, speed)
                                channels.add(
                                    parts[3]
                                )  # Use DeviceLocator for channel count
                        except Exception:
                            continue

                    if max_speed > 0:
                        info["speed"] = max_speed
                    if channels:
                        info["channels"] = len(channels)

        elif platform.system() == "Linux":
            try:
                proc = subprocess.run(
                    ["sudo", "dmidecode", "-t", "memory"],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    channels = set()
                    max_speed = 0
                    for line in proc.stdout.splitlines():
                        line = line.strip()
                        if "Speed:" in line and "Configured" not in line:
                            try:
                                speed = int(line.split(":")[-1].strip().split()[0])
                                max_speed = max(max_speed, speed)
                            except Exception:
                                continue
                        elif "Type:" in line and "Unknown" not in line:
                            info["type"] = line.split(":")[-1].strip()
                        elif "Locator:" in line:
                            channels.add(line.split(":")[-1].strip())

                    if max_speed > 0:
                        info["speed"] = max_speed
                    if channels:
                        info["channels"] = len(channels)
            except Exception:
                pass

    except Exception as e:
        print(f"Error getting RAM info: {e}")

    return info


def get_gpus_info() -> List[Dict]:
    """Get detailed information for all available GPUs."""
    gpus = []
    try:
        # Try NVIDIA GPUs first
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
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

            # Get PCIe info
            pcie_info = pynvml.nvmlDeviceGetMaxPcieLinkGeneration(handle)
            pcie_width = pynvml.nvmlDeviceGetMaxPcieLinkWidth(handle)

            gpus.append(
                {
                    "name": name,
                    "vram_size": info.total // (1024 * 1024),  # Convert to MB
                    "vram_type": vram_type,
                    "tensor_cores": tensor_cores,
                    "cuda_cores": cuda_cores,
                    "compute_capability": f"{compute_cap[0]}.{compute_cap[1]}",
                    "pcie_gen": pcie_info,
                    "pcie_width": f"x{pcie_width}",
                    "index": i,
                }
            )

        pynvml.nvmlShutdown()
    except Exception:
        pass

    return gpus


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


def get_firmware_info() -> Dict:
    """Get firmware and version information."""
    info = {
        "bios_version": "Unknown",
        "bios_vendor": "Unknown",
        "bios_release_date": "Unknown",
        "cpu_microcode": "Unknown",
        "os_name": distro.name() if platform.system() == "Linux" else platform.system(),
        "os_version": (
            distro.version() if platform.system() == "Linux" else platform.version()
        ),
        "os_kernel": platform.release(),
        "ollama_version": "Unknown",
    }

    try:
        # Get OS info
        if platform.system() == "Windows":
            # Get BIOS info using wmic
            proc = subprocess.run(
                [
                    "wmic",
                    "bios",
                    "get",
                    "SMBIOSBIOSVersion,Manufacturer,ReleaseDate",
                    "/format:csv",
                ],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                lines = [
                    line.strip() for line in proc.stdout.split("\n") if line.strip()
                ]
                if len(lines) > 1:  # Skip header
                    try:
                        parts = lines[1].split(",")
                        if len(parts) >= 4:  # Node,Version,Vendor,Date
                            info["bios_version"] = parts[1]
                            info["bios_vendor"] = parts[2]
                            info["bios_release_date"] = parts[3]
                    except Exception:
                        pass  # Keep defaults if parsing fails

        elif platform.system() == "Linux":
            try:
                # Try to get BIOS info from dmidecode
                proc = subprocess.run(
                    ["sudo", "dmidecode", "-t", "bios"],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    for line in proc.stdout.splitlines():
                        line = line.strip()
                        if "Version:" in line:
                            info["bios_version"] = line.split("Version:")[-1].strip()
                        elif "Vendor:" in line:
                            info["bios_vendor"] = line.split("Vendor:")[-1].strip()
                        elif "Release Date:" in line:
                            info["bios_release_date"] = line.split("Release Date:")[
                                -1
                            ].strip()
            except Exception:
                pass  # Keep defaults if dmidecode fails

            try:
                # Get CPU microcode version
                proc = subprocess.run(
                    ["grep", "microcode", "/proc/cpuinfo"],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    info["cpu_microcode"] = proc.stdout.strip().split(":")[-1].strip()
            except Exception:
                pass

        # Try to get Ollama version
        try:
            proc = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                info["ollama_version"] = proc.stdout.strip()
        except Exception:
            pass

    except Exception as e:
        print(f"Error getting firmware info: {e}")

    return info


def get_hardware_info() -> Dict:
    """Get complete hardware information."""
    return {
        "cpu": get_cpu_info(),
        "gpus": get_gpus_info(),
        "ram": get_ram_info(),
        "npu": get_npu_info(),
        "total_memory": psutil.virtual_memory().total // (1024 * 1024),  # Convert to MB
        "firmware": get_firmware_info(),
    }
