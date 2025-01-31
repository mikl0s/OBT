"""Hardware information collection module."""

import datetime
import platform
import re
import subprocess
import winreg
from typing import Dict, List, Optional

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
            channels = 1

            # Get physical memory arrays to determine channels
            for mem_array in w.Win32_PhysicalMemoryArray():
                channels = mem_array.MemoryDevices if mem_array.MemoryDevices else 1

            # Get memory modules
            modules = []
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
                name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")

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
                    "vram_size": info.total // (1024 * 1024),  # Convert to MB
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
                if gpu.AdapterRAM:  # Only include GPUs with memory
                    gpus.append(
                        {
                            "name": gpu.Name,
                            "vram_size": gpu.AdapterRAM
                            // (1024 * 1024),  # Convert to MB
                            "vram_type": "GDDR6X" if "RTX" in gpu.Name else "GDDR6",
                            "pcie_generation": "PCIe 4.0",  # Default for modern GPUs
                            "pcie_width": "x16",
                        }
                    )
        except Exception as e:
            print(f"Error getting GPU info through WMI: {e}")

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
                info["bios_version"] = bios.Version if bios.Version else "Unknown"
                if bios.ReleaseDate:
                    try:
                        # Convert WMI datetime to ISO format
                        date = datetime.strptime(
                            bios.ReleaseDate.split(".")[0], "%Y%m%d%H%M%S"
                        )
                        info["bios_release_date"] = date.isoformat()
                    except ValueError:
                        info["bios_release_date"] = bios.ReleaseDate

            # Get baseboard info for additional details
            for board in w.Win32_BaseBoard():
                if not info["bios_vendor"] or info["bios_vendor"] == "Unknown":
                    info["bios_vendor"] = (
                        board.Manufacturer if board.Manufacturer else "Unknown"
                    )

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
                            info["bios_release_date"] = date.isoformat()
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
    try:
        proc = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception:
        pass
    return "Unknown"
