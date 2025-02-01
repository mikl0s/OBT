"""Hardware information collection module."""

import ctypes
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
import winreg
from datetime import datetime
from typing import Any, Dict, List

import cpuinfo
import psutil


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
    """Get RAM information."""
    try:
        if platform.system() == "Windows":
            import wmi

            w = wmi.WMI()
            total_memory = 0
            ram_type = "Unknown"
            speed = 0
            channels = 1  # Default to single channel

            # Get memory modules
            modules = []
            module_locations = set()
            for mem in w.Win32_PhysicalMemory():
                total_memory += int(mem.Capacity) if mem.Capacity else 0
                if mem.Speed:
                    speed = max(speed, int(mem.Speed))
                if mem.SMBIOSMemoryType:
                    # DDR4 is type 26
                    if mem.SMBIOSMemoryType == 26:
                        ram_type = "DDR4"
                    # DDR5 is type 30
                    elif mem.SMBIOSMemoryType == 30:
                        ram_type = "DDR5"

                # Track unique bank locations to determine channel configuration
                if mem.BankLabel:
                    module_locations.add(mem.BankLabel)

                modules.append(
                    {
                        "capacity": (
                            int(mem.Capacity) // (1024 * 1024) if mem.Capacity else 0
                        ),  # Convert to MB
                        "speed": int(mem.Speed) if mem.Speed else 0,
                        "manufacturer": (
                            mem.Manufacturer if mem.Manufacturer else "Unknown"
                        ),
                        "part_number": (
                            mem.PartNumber.strip() if mem.PartNumber else "Unknown"
                        ),
                    }
                )

            # Determine channel configuration based on populated slots
            # Most modern systems use dual-channel when 2 identical DIMMs are installed
            if len(modules) >= 2 and modules[0]["capacity"] == modules[1]["capacity"]:
                channels = 2  # Dual channel

            return {
                "total": total_memory // (1024 * 1024),  # Convert to MB
                "type": ram_type,
                "speed": speed,
                "channels": channels,
                "modules": modules,
            }
        else:
            # Linux implementation
            total_memory = psutil.virtual_memory().total // (
                1024 * 1024
            )  # Convert to MB

            # Try to get RAM type and speed from dmidecode
            ram_type = "Unknown"
            speed = 0
            channels = 1
            try:
                dmidecode_output = subprocess.check_output(
                    ["dmidecode", "-t", "memory"], universal_newlines=True
                )
                for line in dmidecode_output.split("\n"):
                    if "Type:" in line and "Unknown" not in line:
                        ram_type = line.split(":")[1].strip()
                    elif "Speed:" in line and "Unknown" not in line:
                        try:
                            speed = int(line.split(":")[1].strip().split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif "Number Of Devices:" in line:
                        try:
                            channels = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass
            except (subprocess.CalledProcessError, PermissionError):
                pass

            return {
                "total": total_memory,
                "type": ram_type,
                "speed": speed,
                "channels": channels,
            }

    except Exception as e:
        print(f"Error getting RAM info: {e}")
        return {
            "total": psutil.virtual_memory().total // (1024 * 1024),
            "type": "Unknown",
            "speed": 0,
            "channels": 1,
        }


def get_gpus_info() -> List[Dict]:
    """Get GPU information."""
    gpus = []

    try:
        # Try NVIDIA-SMI first
        import pynvml

        pynvml.nvmlInit()

        try:
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                # Some versions return bytes, others return string
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode("utf-8")

                # Get PCIe info
                pcie_info = pynvml.nvmlDeviceGetMaxPcieLinkGeneration(handle)
                pcie_width = pynvml.nvmlDeviceGetMaxPcieLinkWidth(handle)

                # Get clocks
                graphics_clock = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_GRAPHICS
                )
                memory_clock = pynvml.nvmlDeviceGetClockInfo(
                    handle, pynvml.NVML_CLOCK_MEM
                )

                gpu = {
                    "name": name,
                    "vram_size": round(
                        info.total / (1024 * 1024 * 1024), 2
                    ),  # Convert to GB with 2 decimal places
                    "vram_type": (
                        "GDDR6X" if "RTX" in name else "GDDR6"
                    ),  # Assumption based on RTX series
                    "pcie_generation": f"PCIe {pcie_info}.0",
                    "pcie_width": f"x{pcie_width}",
                    "core_clock": graphics_clock,
                    "memory_clock": memory_clock,
                }

                # Try to get compute capability
                try:
                    major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                    gpu["compute_capability"] = f"{major}.{minor}"
                except pynvml.NVMLError:
                    pass

                gpus.append(gpu)
        except Exception as e:
            print(f"Error getting NVIDIA GPU info: {e}")

    except ImportError:
        print("pynvml not available")
    except Exception as e:
        print(f"Error initializing NVIDIA detection: {e}")

    # If no GPUs found through NVIDIA-SMI, try Windows WMI
    if not gpus and platform.system() == "Windows":
        try:
            import wmi

            w = wmi.WMI()
            for gpu in w.Win32_VideoController():
                # Get VRAM size - try different properties as some might be unavailable
                vram_size = None
                if hasattr(gpu, "AdapterRAM") and gpu.AdapterRAM:
                    vram_size = gpu.AdapterRAM

                if vram_size is not None:
                    gpus.append(
                        {
                            "name": gpu.Name,
                            "vram_size": round(
                                vram_size / (1024 * 1024 * 1024), 2
                            ),  # Convert to GB with 2 decimal places
                            "vram_type": "GDDR6X" if "RTX" in gpu.Name else "GDDR6",
                            "pcie_generation": "PCIe 4.0",  # Default for modern GPUs
                            "pcie_width": "x16",
                        }
                    )
                else:
                    print(f"Could not determine VRAM size for {gpu.Name}")
                    # Try to get VRAM from name (e.g., "NVIDIA GeForce RTX 4070 SUPER 12GB")
                    vram_match = re.search(r"(\d+)\s*GB", gpu.Name)
                    if vram_match:
                        vram_gb = int(vram_match.group(1))
                        gpus.append(
                            {
                                "name": gpu.Name,
                                "vram_size": vram_gb,
                                "vram_type": "GDDR6X" if "RTX" in gpu.Name else "GDDR6",
                                "pcie_generation": "PCIe 4.0",
                                "pcie_width": "x16",
                            }
                        )
                    else:
                        # Add GPU without VRAM info
                        gpus.append(
                            {
                                "name": gpu.Name,
                                "vram_size": None,
                                "vram_type": "GDDR6X" if "RTX" in gpu.Name else "GDDR6",
                                "pcie_generation": "PCIe 4.0",
                                "pcie_width": "x16",
                            }
                        )
        except Exception as e:
            print(f"Error getting GPU info through WMI: {e}")

    return gpus


def get_dxdiag_info() -> Dict[str, Any]:
    """Get GPU and DirectX information from dxdiag on Windows."""
    if platform.system() != "Windows":
        return {}

    try:
        # Create a temporary file for dxdiag output
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
            temp_path = temp.name

        # Run dxdiag and wait for it to complete
        subprocess.run(["dxdiag", "/t", temp_path], check=True)
        time.sleep(1)  # Give it a moment to finish writing

        # Read the dxdiag output
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Clean up temp file
        os.unlink(temp_path)

        info = {
            "gpus": [],
            "directx_version": None,
            "directx_feature_levels": [],
            "wddm_version": None,
        }

        # Parse DirectX version
        dx_match = re.search(r"DirectX Version: (DirectX \d+)", content)
        if dx_match:
            info["directx_version"] = dx_match.group(1)

        # Find all Display Device sections
        gpu_sections = re.finditer(
            r"Card name: (.*?)(?=\n.*?(?:Card name:|$))", content, re.DOTALL
        )

        for gpu in gpu_sections:
            section = gpu.group(0)
            gpu_info = {
                "name": None,
                "manufacturer": None,
                "chip_type": None,
                "device_type": None,
                "device_key": None,
                "device_status": None,
                "dedicated_memory": None,
                "shared_memory": None,
                "feature_levels": None,
                "driver_model": None,
                "driver_version": None,
                "driver_date": None,
                "hardware_scheduling": False,
                "virtualization": None,
                "compute_preemption": None,
                "graphics_preemption": None,
                "hdr_support": None,
                "display_topology": None,
                "dxva2_modes": [],
                "video_memory": None,
            }

            # Extract GPU details
            name_match = re.search(r"Card name: (.+)", section)
            if name_match:
                gpu_info["name"] = name_match.group(1).strip()

            manufacturer_match = re.search(r"Manufacturer: (.+)", section)
            if manufacturer_match:
                gpu_info["manufacturer"] = manufacturer_match.group(1).strip()

            chip_match = re.search(r"Chip type: (.+)", section)
            if chip_match:
                gpu_info["chip_type"] = chip_match.group(1).strip()

            device_type_match = re.search(r"Device Type: (.+)", section)
            if device_type_match:
                gpu_info["device_type"] = device_type_match.group(1).strip()

            device_key_match = re.search(r"Device Key: (.+)", section)
            if device_key_match:
                gpu_info["device_key"] = device_key_match.group(1).strip()

            status_match = re.search(r"Device Status: (.+)", section)
            if status_match:
                gpu_info["device_status"] = status_match.group(1).strip()

            # Memory information
            dedicated_match = re.search(r"Dedicated Memory: (\d+)", section)
            if dedicated_match:
                gpu_info["dedicated_memory"] = int(dedicated_match.group(1))

            shared_match = re.search(r"Shared Memory: (\d+)", section)
            if shared_match:
                gpu_info["shared_memory"] = int(shared_match.group(1))

            total_mem_match = re.search(r"Display Memory: (\d+)", section)
            if total_mem_match:
                gpu_info["video_memory"] = int(total_mem_match.group(1))

            # DirectX features
            feature_match = re.search(r"Feature Levels: (.+)", section)
            if feature_match:
                gpu_info["feature_levels"] = [
                    x.strip() for x in feature_match.group(1).split(",")
                ]

            model_match = re.search(r"Driver Model: (.+)", section)
            if model_match:
                gpu_info["driver_model"] = model_match.group(1).strip()
                wddm_match = re.search(r"WDDM (\d+\.\d+)", model_match.group(1))
                if wddm_match:
                    info["wddm_version"] = wddm_match.group(1)

            driver_match = re.search(r"Driver Version: (.+)", section)
            if driver_match:
                gpu_info["driver_version"] = driver_match.group(1).strip()

            date_match = re.search(r"Driver Date/Size: ([^,]+)", section)
            if date_match:
                gpu_info["driver_date"] = date_match.group(1).strip()

            # Advanced features
            sched_match = re.search(r"Hardware Scheduling: .*Enabled:(\w+)", section)
            if sched_match:
                gpu_info["hardware_scheduling"] = sched_match.group(1).lower() == "true"

            virt_match = re.search(r"Virtualization: (.+)", section)
            if virt_match:
                gpu_info["virtualization"] = virt_match.group(1).strip()

            compute_match = re.search(r"Compute Preemption: (.+)", section)
            if compute_match:
                gpu_info["compute_preemption"] = compute_match.group(1).strip()

            graphics_match = re.search(r"Graphics Preemption: (.+)", section)
            if graphics_match:
                gpu_info["graphics_preemption"] = graphics_match.group(1).strip()

            hdr_match = re.search(r"HDR Support: (.+)", section)
            if hdr_match:
                gpu_info["hdr_support"] = hdr_match.group(1).strip()

            topology_match = re.search(r"Display Topology: (.+)", section)
            if topology_match:
                gpu_info["display_topology"] = topology_match.group(1).strip()

            # Video acceleration features
            dxva2_match = re.search(
                r"DXVA2 Modes: (.+?)(?=\n\s+[A-Za-z]|$)", section, re.DOTALL
            )
            if dxva2_match:
                modes = re.findall(r"DXVA2_Mode(\w+)", dxva2_match.group(1))
                gpu_info["dxva2_modes"] = modes

            info["gpus"].append(gpu_info)

        return info

    except Exception as e:
        print(f"Error getting dxdiag info: {e}")
        return {}


def get_npu_info() -> Dict:
    """Get NPU (Neural Processing Unit) information if available."""
    info = {
        "type": "none",
        "name": "none",
        "compute_capability": None,
        "cores": None,
        "memory": None,
        "driver_version": None,
        "tensor_cores": False,
        "fp16_support": False,
        "directx": None,
        "video_acceleration": None,
    }

    system = platform.system()

    # Check for NVIDIA GPU with compute capability
    try:
        # Ensure NVML is loaded correctly on Windows
        if system == "Windows":
            os.add_dll_directory("C:\\Windows\\System32")
            ctypes.WinDLL("C:\\Windows\\System32\\nvml.dll")

        import pynvml

        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
            info["type"] = "cuda"
            info["name"] = (
                pynvml.nvmlDeviceGetName(handle).decode("utf-8")
                if isinstance(pynvml.nvmlDeviceGetName(handle), bytes)
                else pynvml.nvmlDeviceGetName(handle)
            )
            info["compute_capability"] = f"{major}.{minor}"
            info["cores"] = (
                pynvml.nvmlDeviceGetNumGpuCores(handle)
                if hasattr(pynvml, "nvmlDeviceGetNumGpuCores")
                else None
            )
            info["memory"] = pynvml.nvmlDeviceGetMemoryInfo(handle).total // (
                1024 * 1024
            )  # Convert to MB
            info["driver_version"] = (
                pynvml.nvmlSystemGetDriverVersion().decode()
                if isinstance(pynvml.nvmlSystemGetDriverVersion(), bytes)
                else pynvml.nvmlSystemGetDriverVersion()
            )
            info["tensor_cores"] = float(info["compute_capability"]) >= 7.0
            info["fp16_support"] = float(info["compute_capability"]) >= 7.0

            # Get DirectX info for Windows
            if system == "Windows":
                dx_info = get_dxdiag_info()
                if dx_info and dx_info["gpus"]:
                    # Find matching GPU in dxdiag output
                    for gpu in dx_info["gpus"]:
                        if info["name"] in gpu["name"]:
                            info["directx"] = {
                                "version": dx_info["directx_version"],
                                "feature_levels": gpu["feature_levels"],
                                "driver_model": gpu["driver_model"],
                                "hardware_scheduling": gpu["hardware_scheduling"],
                                "compute_preemption": gpu["compute_preemption"],
                                "graphics_preemption": gpu["graphics_preemption"],
                                "virtualization": gpu["virtualization"],
                                "device_type": gpu["device_type"],
                            }
                            # Add video acceleration capabilities
                            if gpu["dxva2_modes"]:
                                info["video_acceleration"] = {
                                    "dxva2_modes": gpu["dxva2_modes"],
                                    "hdr_support": gpu["hdr_support"],
                                }
                            break
    except Exception as e:
        print(f"Error getting NVIDIA NPU info: {e}")

    # Check for AMD GPU on Linux
    if info["type"] == "none" and system == "Linux":
        try:
            result = subprocess.run(["rocm-smi", "-a"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                info["type"] = "rocm"
                # Parse rocm-smi output for device info
                for line in result.stdout.splitlines():
                    if "GPU[" in line:
                        info["name"] = line.split(":")[1].strip()
                    elif "Memory" in line:
                        mem_match = re.search(r"(\d+)MB", line)
                        if mem_match:
                            info["memory"] = int(mem_match.group(1))
        except FileNotFoundError:
            print("ROCm not installed, skipping AMD GPU detection")
        except Exception as e:
            print(f"Error getting AMD GPU info: {e}")

    # Check for Intel/AMD GPUs on Windows using dxdiag
    if info["type"] == "none" and system == "Windows":
        try:
            dx_info = get_dxdiag_info()
            if dx_info and dx_info["gpus"]:
                gpu = dx_info["gpus"][0]  # Use primary GPU
                info["type"] = "gpu"
                info["name"] = gpu["name"]
                info["memory"] = gpu["video_memory"]  # Use total video memory
                info["driver_version"] = gpu["driver_version"]

                # Check for known AI accelerators
                name_lower = gpu["name"].lower()
                if "neural" in name_lower or "npu" in name_lower or "ai" in name_lower:
                    info["type"] = "npu"

                # Add DirectX capabilities
                info["directx"] = {
                    "version": dx_info["directx_version"],
                    "feature_levels": gpu["feature_levels"],
                    "driver_model": gpu["driver_model"],
                    "hardware_scheduling": gpu["hardware_scheduling"],
                    "compute_preemption": gpu["compute_preemption"],
                    "graphics_preemption": gpu["graphics_preemption"],
                    "virtualization": gpu["virtualization"],
                    "device_type": gpu["device_type"],
                }

                # Add video acceleration capabilities
                if gpu["dxva2_modes"]:
                    info["video_acceleration"] = {
                        "dxva2_modes": gpu["dxva2_modes"],
                        "hdr_support": gpu["hdr_support"],
                    }

                # Infer capabilities from GPU and driver features
                if gpu["feature_levels"] and any(
                    level.startswith("12_") for level in gpu["feature_levels"]
                ):
                    info["fp16_support"] = True

                # Check for NPU capabilities based on device type and features
                if (
                    gpu["device_type"] == "Full Device (POST)"
                    and gpu["hardware_scheduling"]
                    and gpu["compute_preemption"] == "Dispatch"
                ):
                    info["type"] = "npu"

        except Exception as e:
            print(f"Error getting Windows GPU info: {e}")

    # Check for Apple Neural Engine on M1/M2 Macs
    if info["type"] == "none" and system == "Darwin":
        try:
            result = subprocess.run(["sysctl", "-a"], capture_output=True, text=True)
            if result.returncode == 0 and "machdep.cpu" in result.stdout:
                info["type"] = "ane"
                info["name"] = "Apple Neural Engine"
                # Try to get more details about the chip
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPHardwareDataType"],
                        capture_output=True,
                        text=True,
                    )
                    if "Chip" in result.stdout:
                        for line in result.stdout.splitlines():
                            if "Chip" in line:
                                info["name"] = (
                                    f"Apple Neural Engine ({line.split(':')[1].strip()})"
                                )
                except Exception:
                    pass
        except Exception as e:
            print(f"Error getting Apple Neural Engine info: {e}")

    # Check for other NPUs on Linux (Intel Movidius, AMD Ryzen AI, etc.)
    if info["type"] == "none" and system == "Linux":
        try:
            result = subprocess.run(["lspci"], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout.lower()
                if "movidius" in output:
                    info["type"] = "movidius"
                    info["name"] = "Intel Movidius VPU"
                elif "ryzen ai" in output:
                    info["type"] = "ryzen_ai"
                    info["name"] = "AMD Ryzen AI NPU"
                elif "hexagon" in output:
                    info["type"] = "hexagon"
                    info["name"] = "Qualcomm Hexagon DSP"
        except Exception as e:
            print(f"Error detecting Linux NPUs: {e}")

    return info


def get_directml_info() -> Dict[str, Any]:
    """Get DirectML information from Windows Registry and DLL checks."""
    info = {"available": False, "version": None, "capabilities": [], "dll_path": None}

    if platform.system() != "Windows":
        return info

    try:
        # Check Windows Registry for DirectML
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\DirectML"
            )
            info["version"] = winreg.QueryValueEx(key, "Version")[0]
            info["available"] = True
            winreg.CloseKey(key)
        except WindowsError:
            # Try checking System32 for DirectML DLL directly
            dll_path = os.path.join(
                os.environ["SystemRoot"], "System32", "DirectML.dll"
            )
            if os.path.exists(dll_path):
                info["available"] = True
                info["dll_path"] = dll_path
                # Try to get version from DLL
                try:
                    import pefile

                    pe = pefile.PE(dll_path)
                    info["version"] = (
                        f"{pe.FileInfo[0].StringTable[0].entries[b'FileVersion'].decode()}"
                    )
                except Exception:
                    pass

        # Check for DirectML device capabilities
        if info["available"]:
            import wmi

            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                driver_path = gpu.DriverPath if hasattr(gpu, "DriverPath") else None
                if driver_path and "directml" in driver_path.lower():
                    # Device supports DirectML
                    caps = []

                    # Check for known DirectML capabilities based on driver and device
                    if (
                        gpu.AdapterDACType
                        and "integrated" not in gpu.AdapterDACType.lower()
                    ):
                        caps.append("hardware_acceleration")

                    # Intel GPUs usually support these
                    if "intel" in gpu.Name.lower():
                        caps.extend(["fp16", "int8"])
                        if "arc" in gpu.Name.lower() or "xe" in gpu.Name.lower():
                            caps.extend(["dp4a", "neural_network"])

                    # AMD GPUs
                    elif "amd" in gpu.Name.lower() or "radeon" in gpu.Name.lower():
                        caps.extend(["fp16"])
                        if "rdna" in gpu.Name.lower() or "navi" in gpu.Name.lower():
                            caps.extend(["neural_network"])

                    info["capabilities"] = list(set(caps))  # Remove duplicates
                    break

    except Exception as e:
        print(f"Error getting DirectML info: {e}")

    return info


def get_firmware_info() -> Dict:
    """Get firmware and system information."""
    info = {
        "os_name": platform.system(),
        "os_version": platform.version(),
        "os_kernel": platform.release(),
        "bios_vendor": "Unknown",
        "bios_version": "Unknown",
        "bios_release_date": "Unknown",
        "cpu_microcode": "Unknown",
        "ollama_version": get_ollama_version(),
    }

    try:
        if platform.system() == "Windows":
            import wmi

            w = wmi.WMI()

            # Get BIOS info
            for bios in w.Win32_BIOS():
                info["bios_vendor"] = (
                    bios.Manufacturer if bios.Manufacturer else "Unknown"
                )
                # Try to extract the short version (like A.Q1) from the full version string
                version = bios.Version if bios.Version else "Unknown"
                if version != "Unknown":
                    # Try to find version in format X.XX or X.X
                    version_match = re.search(r"[A-Z]\.[A-Z0-9]+", version)
                    if version_match:
                        version = version_match.group(0)
                info["bios_version"] = version

                if bios.ReleaseDate:
                    try:
                        # Convert WMI datetime format (YYYYMMDDHHMMSS.MMMMMM+UUU) to ISO
                        date_str = bios.ReleaseDate.split(".")
                        date = datetime.strptime(date_str[0], "%Y%m%d%H%M%S")
                        info["bios_release_date"] = date.strftime("%Y-%m-%d")
                    except (ValueError, AttributeError):
                        info["bios_release_date"] = bios.ReleaseDate

            # Get baseboard info for additional details
            for board in w.Win32_BaseBoard():
                if not info["bios_vendor"] or info["bios_vendor"] == "Unknown":
                    info["bios_vendor"] = (
                        board.Manufacturer if board.Manufacturer else "Unknown"
                    )
                    # Try to get version from product name if BIOS version is still unknown
                    if info["bios_version"] == "Unknown" and board.Product:
                        version_match = re.search(r"[A-Z]\.[A-Z0-9]+", board.Product)
                        if version_match:
                            info["bios_version"] = version_match.group(0)

            # Try to get CPU microcode version
            try:
                reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(
                    reg, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
                )
                info["cpu_microcode"] = str(
                    winreg.QueryValueEx(key, "Update Revision")[0]
                )
            except Exception:
                pass

        else:
            # Linux implementation
            try:
                # Get BIOS info using dmidecode
                dmidecode_output = subprocess.check_output(
                    ["dmidecode", "-t", "bios"], universal_newlines=True
                )
                for line in dmidecode_output.split("\n"):
                    if "Vendor:" in line:
                        info["bios_vendor"] = line.split(":")[1].strip()
                    elif "Version:" in line:
                        info["bios_version"] = line.split(":")[1].strip()
                    elif "Release Date:" in line:
                        date_str = line.split(":")[1].strip()
                        try:
                            date = datetime.strptime(date_str, "%m/%d/%Y")
                            info["bios_release_date"] = date.strftime("%Y-%m-%d")
                        except ValueError:
                            info["bios_release_date"] = date_str

                # Try to get CPU microcode version
                proc = subprocess.run(
                    ["grep", "microcode", "/proc/cpuinfo"],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0 and proc.stdout:
                    info["cpu_microcode"] = proc.stdout.split(":")[1].strip()
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


def get_ollama_version() -> str:
    """Get Ollama version using multiple methods."""
    if platform.system() == "Windows":
        # Find ollama executable path
        exe_path = shutil.which("ollama.exe")
        if not exe_path:
            print("Ollama executable not found in PATH")
            return "Unknown"

        # Method 1: Try Windows Registry (no admin required)
        try:
            registry_path = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Ollama"
            )
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as key:
                version = winreg.QueryValueEx(key, "DisplayVersion")[0]
                if version:
                    return version
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error reading registry: {e}")

        # Method 2: Try win32api (built into Windows)
        try:
            import win32api

            info = win32api.GetFileVersionInfo(exe_path, "\\")
            ms = info["FileVersionMS"]
            ls = info["FileVersionLS"]
            version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            return version
        except ImportError:
            pass
        except Exception as e:
            print(f"Error reading version with win32api: {e}")

        # Method 3: Try pefile (if installed)
        try:
            import pefile

            pe = pefile.PE(exe_path)
            for file_info in pe.FileInfo:
                for entry in file_info:
                    if entry.Key == b"StringFileInfo":
                        for st in entry.StringTable:
                            if "FileVersion" in st.entries:
                                return st.entries["FileVersion"].decode()
        except ImportError:
            pass
        except Exception as e:
            print(f"Error reading version with pefile: {e}")

    # Fallback for non-Windows or if all Windows methods fail
    try:
        proc = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass

    return "Unknown"
