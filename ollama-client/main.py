"""Ollama client that connects to OBT server."""

import asyncio
import logging
import signal
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import psutil
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

__version__ = "0.3.2"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info(f"Starting Ollama Client v{__version__}")

# Global flag for graceful shutdown
shutdown_event = asyncio.Event()

# Store registration ID
registration_id: Optional[str] = None


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received, cleaning up...")
    shutdown_event.set()


# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


class Settings(BaseSettings):
    """Application settings."""

    CLIENT_ID: str = Field(default="default", env="CLIENT_ID")
    OBT_SERVER_URL: str = Field(default="http://localhost:8881", env="OBT_SERVER_URL")
    OLLAMA_URL: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    HEARTBEAT_INTERVAL: int = Field(
        default=10, description="Heartbeat interval in seconds"
    )
    registration_id: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields in .env and environment variables


settings = Settings()


class OllamaModel(BaseModel):
    """Ollama model information."""

    name: str
    tags: List[str] = []
    size: int = 0
    modified: float
    version: str = "unknown"

    class Config:
        json_encoders = {float: lambda v: v}


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


class NPUInfo(BaseModel):
    """Neural Processing Unit information."""

    name: Optional[str] = Field(None, description="NPU name/model")
    compute_power: Optional[float] = Field(None, description="Compute power in TOPS")
    precision_support: Optional[List[str]] = Field(
        None, description="Supported precision formats"
    )
    dedicated: Optional[bool] = Field(None, description="Whether it's a dedicated NPU")


class HardwareInfo(BaseModel):
    """Complete system hardware information."""

    cpu: CPUInfo = Field(..., description="CPU information")
    gpu: Optional[GPUInfo] = Field(None, description="GPU information if available")
    npu: Optional[NPUInfo] = Field(None, description="NPU information if available")
    total_memory: int = Field(..., description="Total system memory in MB")
    ram: Dict = Field(..., description="Detailed RAM information")
    firmware: Dict = Field(..., description="Firmware and version information")


class BenchmarkConfig(BaseModel):
    """Benchmark configuration."""

    model_name: str
    prompt_config: dict
    hardware: dict
    num_iterations: int = 3


class BenchmarkMetrics(BaseModel):
    """Benchmark metrics."""

    tokens_per_second: float = 0
    latency_ms: float = 0
    memory_usage_mb: float = 0
    cpu_usage_percent: float = 0
    gpu_memory_usage_mb: Optional[float] = None
    gpu_usage_percent: Optional[float] = None


class BenchmarkResult(BaseModel):
    """Benchmark result."""

    benchmark_id: str
    client_id: str
    config: BenchmarkConfig
    hardware_info: HardwareInfo
    metrics: List[BenchmarkMetrics]
    start_time: datetime
    end_time: datetime
    status: str = "running"
    error: Optional[str] = None


async def check_ollama_connection() -> bool:
    """Check if Ollama is available."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False


async def get_installed_models() -> List[OllamaModel]:
    """Get list of installed models from Ollama."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
            if response.status != 200:
                raise Exception(f"Failed to get models: {await response.text()}")
            data = await response.json()
            models = []
            for model in data.get("models", []):
                # Ensure we have a valid timestamp, default to current time if missing
                modified = model.get("modified", 0)
                if not modified or modified < 0:
                    modified = int(datetime.now().timestamp())

                models.append(
                    OllamaModel(
                        name=model["name"],
                        tags=model.get("tags", []),
                        size=model.get("size", 0),
                        modified=modified,
                        version=model.get("version", "unknown"),
                    )
                )
            return models


async def get_hardware_info() -> HardwareInfo:
    """Get hardware information."""
    try:
        import hardware_info

        return HardwareInfo(**hardware_info.get_hardware_info())
    except Exception as e:
        logger.error(f"Error getting hardware info: {e}")
        # Return minimal info to avoid registration failure
        return HardwareInfo(
            cpu=CPUInfo(
                name="Unknown CPU",
                architecture="unknown",
                base_clock=1.0,
                cores=1,
                threads=1,
                features=[],
            ),
            total_memory=1024,  # 1GB in MB
            ram={},
            firmware={},
        )


async def register_with_server() -> bool:
    """Register with OBT server."""
    try:
        # Get hardware info first
        hardware = await get_hardware_info()
        logger.debug(f"Hardware info: {hardware.model_dump_json()}")

        # Build registration URL
        registration_url = (
            f"{settings.OBT_SERVER_URL}/api/v1/models/register"
            f"?client_id={settings.CLIENT_ID}&version={__version__}"
        )
        logger.debug(f"Registration URL: {registration_url}")

        # Send registration request with hardware info
        async with aiohttp.ClientSession() as session:
            async with session.post(
                registration_url,
                json={"hardware": hardware.model_dump()},
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to register: {error_text}")
                    return False
                data = await response.json()
                settings.registration_id = data.get("registration_id")
                logger.info(f"Registered with ID: {settings.registration_id}")
                return True
    except Exception as e:
        logger.error(f"Failed to register: {e}")
        return False


async def send_heartbeat() -> bool:
    """Send heartbeat to server with current status."""
    try:
        ollama_available = await check_ollama_connection()
        models = await get_installed_models() if ollama_available else []

        # Convert models to dict and handle Pydantic deprecation
        models_data = [model.model_dump() for model in models]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.OBT_SERVER_URL}/api/v1/models/heartbeat",
                params={
                    "client_id": settings.CLIENT_ID,
                    "version": __version__,
                    "available": str(ollama_available).lower(),
                },
                json={
                    "models": models_data,
                },
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to send heartbeat: {await response.text()}")
                    return False
                return True
    except Exception as e:
        logger.error(f"Failed to send heartbeat: {e}")
        return False


async def run_benchmark(benchmark_id: str, config: BenchmarkConfig) -> None:
    """Run a benchmark and report results to server."""
    try:
        # Initialize result
        hardware = await get_hardware_info()
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            client_id=settings.CLIENT_ID,
            config=config,
            hardware_info=hardware,
            metrics=[],
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="running",
        )

        # Send initial status
        await _report_benchmark_result(result)

        # Run benchmark
        metrics = []
        for _ in range(config.num_iterations):
            start_time = datetime.now().timestamp()

            # Run model inference
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": config.model_name,
                        "prompt": config.prompt_config["prompt"],
                        "options": {"num_gpu": 1 if hardware.cpu.threads > 1 else 0},
                    },
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {await response.text()}")
                    data = await response.json()

            # Calculate metrics
            end_time = datetime.now().timestamp()
            duration = end_time - start_time
            tokens = len(data["response"].split())

            metrics.append(
                BenchmarkMetrics(
                    tokens_per_second=tokens / duration,
                    latency_ms=duration * 1000,
                    memory_usage_mb=psutil.Process().memory_info().rss / (1024 * 1024),
                    cpu_usage_percent=psutil.cpu_percent(),
                    gpu_memory_usage_mb=(
                        hardware.gpu.vram_size if hardware.gpu else None
                    ),
                    gpu_usage_percent=(
                        100 if hardware.gpu else None
                    ),  # Ollama uses 100% GPU when active
                )
            )

            # Short cooldown between iterations
            await asyncio.sleep(1)

        # Update and send final result
        result.metrics = metrics
        result.end_time = datetime.now()
        result.status = "completed"
        await _report_benchmark_result(result)

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        result.status = "failed"
        result.error = str(e)
        await _report_benchmark_result(result)


async def _report_benchmark_result(result: BenchmarkResult) -> None:
    """Report benchmark result to server."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.OBT_SERVER_URL}/api/v1/benchmarks/update",
                json=result.model_dump(),
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Failed to report benchmark result: {await response.text()}"
                    )
    except Exception as e:
        logger.error(f"Failed to report benchmark result: {e}")


async def heartbeat_loop():
    """Main heartbeat loop."""
    logger.info(f"Connecting to OBT server at {settings.OBT_SERVER_URL}")

    while not shutdown_event.is_set():
        if not await register_with_server():
            logger.error("Failed to register, retrying in 10 seconds...")
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=10)
            except asyncio.TimeoutError:
                continue
            continue

        while not shutdown_event.is_set():
            if not await send_heartbeat():
                break
            try:
                await asyncio.wait_for(
                    shutdown_event.wait(), timeout=settings.HEARTBEAT_INTERVAL
                )
            except asyncio.TimeoutError:
                continue

    logger.info("Heartbeat loop stopped")


async def main():
    """Main entry point."""
    try:
        await heartbeat_loop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down client...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled by signal handler
    logger.info("Client stopped")
