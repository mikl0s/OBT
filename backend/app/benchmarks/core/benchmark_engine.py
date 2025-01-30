import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional

import GPUtil
import psutil

from ...services.ollama import OllamaService
from ..schemas.benchmark import (
    BenchmarkConfig,
    BenchmarkMetrics,
    BenchmarkResult,
    GPUInfo,
    HardwareInfo,
)


class BenchmarkEngine:
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service
        self._running_benchmarks: Dict[str, asyncio.Task] = {}

    def _get_hardware_info(self) -> HardwareInfo:
        """Collect system hardware information."""
        psutil.cpu_freq()
        gpu_devices = GPUtil.getGPUs()

        gpus = []
        for gpu in gpu_devices:
            gpus.append(
                GPUInfo(
                    id=gpu.id,
                    name=gpu.name,
                    memory_total=gpu.memoryTotal,
                    memory_free=gpu.memoryFree,
                    utilization=gpu.load,
                )
            )

        return HardwareInfo(
            cpu_model=psutil.cpu_freq()._asdict().get("current", 0),
            cpu_cores=psutil.cpu_count(logical=False),
            cpu_threads=psutil.cpu_count(logical=True),
            ram_total=psutil.virtual_memory().total // (1024 * 1024),  # MB
            gpus=gpus,
        )

    async def _collect_metrics(
        self, start_time: float, gpu_id: Optional[int] = None
    ) -> BenchmarkMetrics:
        """Collect system performance metrics."""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.Process().memory_info()
        gpu_devices = GPUtil.getGPUs()

        metrics = BenchmarkMetrics(
            tokens_per_second=0,  # Will be updated later
            latency_ms=0,  # Will be updated later
            memory_usage_mb=memory.rss / (1024 * 1024),
            cpu_usage_percent=cpu_percent,
        )

        if gpu_id is not None and gpu_devices:
            for gpu in gpu_devices:
                if gpu.id == gpu_id:
                    metrics.gpu_memory_usage_mb = gpu.memoryUsed
                    metrics.gpu_usage_percent = gpu.load * 100
                    break

        return metrics

    async def run_benchmark(
        self, client_id: str, config: BenchmarkConfig
    ) -> BenchmarkResult:
        """Run a benchmark with the given configuration."""
        # Initialize result
        result = BenchmarkResult(
            client_id=client_id,
            config=config,
            hardware_info=self._get_hardware_info(),
            metrics=[],
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="running",
        )

        try:
            # Generate sample prompt
            prompt = (
                "Generate a detailed technical analysis of the following topic: "
                * config.prompt_tokens
            )

            # Set hardware configuration for Ollama
            hardware_config = {"use_gpu": config.hardware.use_gpu}
            if config.hardware.gpu_id is not None:
                hardware_config["gpu_id"] = config.hardware.gpu_id

            # Run benchmark iterations
            for _ in range(config.num_iterations):
                start_time = time.time()

                # Run model inference with hardware selection
                response = await self.ollama_service.generate(
                    model=config.model_name,
                    prompt=prompt,
                    client_id=client_id,
                    options={
                        "temperature": config.temperature,
                        "top_p": config.top_p,
                        "top_k": config.top_k,
                        "repeat_penalty": config.repeat_penalty,
                        **hardware_config,
                    },
                )

                end_time = time.time()

                # Collect metrics with GPU info if selected
                metrics = await self._collect_metrics(
                    start_time,
                    config.hardware.gpu_id if config.hardware.use_gpu else None,
                )
                metrics.latency_ms = (end_time - start_time) * 1000
                metrics.tokens_per_second = len(response) / (end_time - start_time)

                result.metrics.append(metrics)

                # Small delay between iterations
                await asyncio.sleep(1)

            result.status = "completed"
            result.end_time = datetime.now()

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            result.end_time = datetime.now()

        return result

    async def start_benchmark(self, client_id: str, config: BenchmarkConfig) -> str:
        """Start a benchmark asynchronously."""
        benchmark_task = asyncio.create_task(self.run_benchmark(client_id, config))
        self._running_benchmarks[config.model_name] = benchmark_task
        return config.model_name

    def get_running_benchmarks(self) -> List[str]:
        """Get list of currently running benchmark model names."""
        return list(self._running_benchmarks.keys())

    async def get_benchmark_status(self, model_name: str) -> Optional[BenchmarkResult]:
        """Get the status of a running benchmark."""
        task = self._running_benchmarks.get(model_name)
        if not task:
            return None

        if task.done():
            del self._running_benchmarks[model_name]
            return await task

        return None
