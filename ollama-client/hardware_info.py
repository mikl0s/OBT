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
    try:
        if platform.system() == "Windows":
            # Use wmic to get RAM info on Windows
            ram_info = {"speed": 0, "type": "Unknown", "channels": 1, "modules": []}

            # Get RAM type and speed
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
                    modules = []
                    channels = set()
                    max_speed = 0
                    for line in lines[1:]:
                        if not line:
                            continue
                        _, speed, mem_type, location, capacity = line.split(",")
                        speed = int(speed) if speed.isdigit() else 0
                        max_speed = max(max_speed, speed)

                        # Determine RAM type
                        mem_types = {
                            20: "DDR",
                            21: "DDR2",
                            22: "DDR2 FB-DIMM",
                            24: "DDR3",
                            26: "DDR4",
                            27: "DDR5",
                        }
                        ram_type = (
                            mem_types.get(int(mem_type), "Unknown")
                            if mem_type.isdigit()
                            else "Unknown"
                        )

                        # Extract channel from location (e.g., "DIMM 1" -> Channel 1)
                        channel = re.search(r"\d+", location)
                        if channel:
                            channels.add(int(channel.group()))

                        modules.append(
                            {
                                "size": int(capacity) // (1024 * 1024),  # Convert to MB
                                "speed": speed,
                                "location": location,
                                "type": ram_type,
                            }
                        )

                    ram_info.update(
                        {
                            "speed": max_speed,
                            "type": ram_type,
                            "channels": len(channels),
                            "modules": modules,
                        }
                    )
        else:
            # Use dmidecode on Linux (requires root)
            ram_info = {"speed": 0, "type": "Unknown", "channels": 1, "modules": []}

            try:
                proc = subprocess.run(
                    ["sudo", "dmidecode", "--type", "memory"],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    modules = []
                    channels = set()
                    max_speed = 0
                    current_module = {}

                    for line in proc.stdout.split("\n"):
                        line = line.strip()
                        if "Memory Device" in line:
                            if current_module:
                                modules.append(current_module)
                            current_module = {}
                        elif "Size:" in line:
                            size = re.search(r"Size: (\d+) ([GM]B)", line)
                            if size:
                                value, unit = size.groups()
                                value = int(value)
                                if unit == "GB":
                                    value *= 1024
                                current_module["size"] = value
                        elif "Type:" in line and "Unknown" not in line:
                            current_module["type"] = line.split(": ")[1]
                        elif "Speed:" in line:
                            speed = re.search(r"(\d+)", line)
                            if speed:
                                speed = int(speed.group(1))
                                current_module["speed"] = speed
                                max_speed = max(max_speed, speed)
                        elif "Locator:" in line:
                            location = line.split(": ")[1]
                            current_module["location"] = location
                            channel = re.search(r"\d+", location)
                            if channel:
                                channels.add(int(channel.group()))

                    if current_module:
                        modules.append(current_module)

                    ram_info.update(
                        {
                            "speed": max_speed,
                            "type": modules[0]["type"] if modules else "Unknown",
                            "channels": len(channels),
                            "modules": modules,
                        }
                    )
            except Exception:
                pass

        return ram_info
    except Exception:
        return {"speed": 0, "type": "Unknown", "channels": 1, "modules": []}


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
        "os_name": "",
        "os_version": "",
        "os_kernel": "",
        "ollama_version": "Unknown",
    }

    try:
        # Get OS info
        if platform.system() == "Windows":
            info["os_name"] = "Windows"
            info["os_version"] = platform.version()
            info["os_kernel"] = platform.release()

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
                    _, version, vendor, date = lines[1].split(",")
                    info["bios_version"] = version
                    info["bios_vendor"] = vendor
                    info["bios_release_date"] = date
        else:
            # Get Linux distribution info
            info["os_name"] = distro.name(pretty=True)
            info["os_version"] = distro.version(pretty=True)
            info["os_kernel"] = platform.release()

            # Get BIOS info using dmidecode
            try:
                proc = subprocess.run(
                    ["sudo", "dmidecode", "-t", "bios"],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    for line in proc.stdout.split("\n"):
                        line = line.strip()
                        if "Version:" in line:
                            info["bios_version"] = line.split("Version:", 1)[1].strip()
                        elif "Vendor:" in line:
                            info["bios_vendor"] = line.split("Vendor:", 1)[1].strip()
                        elif "Release Date:" in line:
                            info["bios_release_date"] = line.split("Release Date:", 1)[
                                1
                            ].strip()
            except Exception:
                pass

        # Get CPU microcode version
        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "microcode" in line:
                            info["cpu_microcode"] = line.split(":")[1].strip()
                            break
            except Exception:
                pass
        elif platform.system() == "Windows":
            try:
                proc = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-WmiObject -Class Win32_Processor | Select-Object -ExpandProperty Description",
                    ],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0:
                    # Try to extract microcode version from CPU description
                    match = re.search(r"Microcode Revision: (\d+)", proc.stdout)
                    if match:
                        info["cpu_microcode"] = match.group(1)
            except Exception:
                pass

        # Get Ollama version
        try:
            proc = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                info["ollama_version"] = proc.stdout.strip()
        except Exception:
            # Try alternative method for Windows
            if platform.system() == "Windows":
                try:
                    proc = subprocess.run(
                        [
                            "powershell",
                            "-Command",
                            "(Get-Item (Get-Command ollama).Source).VersionInfo.FileVersion",
                        ],
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
