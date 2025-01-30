"""Ollama client that connects to OBT server."""

import asyncio
import logging
import signal
from datetime import datetime
from typing import List, Optional

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

    OBT_SERVER_URL: str = Field(default="http://localhost:8881")
    OLLAMA_URL: str = Field(default="http://localhost:11434")
    CLIENT_ID: str = Field(default="default-client")
    HEARTBEAT_INTERVAL: int = Field(default=10)  # seconds

    class Config:
        env_file = ".env"
        # Allow extra fields in .env to support legacy configs
        extra = "ignore"


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


class HardwareInfo(BaseModel):
    """Hardware information from Ollama."""

    cpu_threads: int = Field(default=None, description="Number of CPU threads")
    gpu_count: int = Field(default=0, description="Number of GPUs")
    gpu_name: str = Field(default=None, description="GPU name if available")
    gpu_memory: int = Field(default=None, description="GPU memory in MB if available")


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
    """Get hardware information from Ollama."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.OLLAMA_URL}/api/show") as response:
                if response.status != 200:
                    return HardwareInfo()
                data = await response.json()
                return HardwareInfo(
                    cpu_threads=data.get("cpu_threads"),
                    gpu_count=1 if data.get("gpu_info") else 0,
                    gpu_name=data.get("gpu_info", {}).get("name"),
                    gpu_memory=data.get("gpu_info", {}).get("memory"),
                )
    except Exception as e:
        logger.error(f"Failed to get hardware info: {e}")
        return HardwareInfo()


async def register_with_server() -> bool:
    """Register this client with the OBT server."""
    try:
        logger.info(
            f"Registering with OBT server as {settings.CLIENT_ID} "
            f"(version {__version__})"
        )
        params = {
            "client_id": settings.CLIENT_ID,
            "version": __version__,
        }
        url = f"{settings.OBT_SERVER_URL}/api/v1/models/register"
        logger.debug(
            f"Registration URL: {url}?"
            f"client_id={params['client_id']}&"
            f"version={params['version']}"
        )

        # Get hardware info for registration
        hardware = await get_hardware_info()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params=params,
                json={"hardware": hardware.model_dump()},
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to register: {await response.text()}")
                    return False

                data = await response.json()
                global registration_id
                registration_id = data["registration_id"]
                logger.info(
                    f"Successfully registered with OBT server. Registration ID: {registration_id}"
                )
                return True
    except Exception as e:
        logger.error(f"Failed to register with server: {e}")
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
                        "options": {"num_gpu": 1 if hardware.gpu_count > 0 else 0},
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
                        hardware.gpu_memory if hardware.gpu_memory else None
                    ),
                    gpu_usage_percent=(
                        100 if hardware.gpu_count > 0 else None
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
