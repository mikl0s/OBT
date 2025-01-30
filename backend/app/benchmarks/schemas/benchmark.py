from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class GPUInfo(BaseModel):
    id: int
    name: str
    memory_total: int
    memory_free: int
    utilization: float


class HardwareInfo(BaseModel):
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    ram_total: int
    gpus: List[GPUInfo] = []


class HardwareSelection(BaseModel):
    use_gpu: bool = True
    gpu_id: Optional[int] = None


class TestPromptConfig(BaseModel):
    suite_name: str
    prompt_name: str
    completion_tokens: int = Field(default=100, ge=1)


class CustomPromptConfig(BaseModel):
    prompt: str
    completion_tokens: int = Field(default=100, ge=1)


class BenchmarkConfig(BaseModel):
    model_name: str
    prompt_config: Union[TestPromptConfig, CustomPromptConfig]
    num_iterations: int = Field(
        default=3, ge=1, description="Number of times to run the benchmark"
    )
    temperature: float = Field(default=0.7, ge=0, le=1)
    top_p: float = Field(default=1.0, ge=0, le=1)
    top_k: int = Field(default=40, ge=0)
    repeat_penalty: float = Field(default=1.1, ge=0)
    hardware: HardwareSelection = Field(default_factory=HardwareSelection)


class DetailedMetrics(BaseModel):
    tokens_per_second: float
    first_token_ms: float
    average_token_ms: float
    total_duration_ms: float
    memory_usage_mb: float
    gpu_memory_usage_mb: Optional[float] = None
    cpu_usage_percent: float
    gpu_usage_percent: Optional[float] = None
    cpu_temperature: Optional[float] = None
    gpu_temperature: Optional[float] = None
    power_usage_watts: Optional[float] = None


class BenchmarkMetrics(DetailedMetrics):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class BenchmarkResult(BaseModel):
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    client_id: str
    config: BenchmarkConfig
    hardware_info: HardwareInfo
    metrics: List[BenchmarkMetrics]
    start_time: datetime
    end_time: datetime
    status: str = "completed"
    error: Optional[str] = None

    @property
    def average_tokens_per_second(self) -> float:
        return sum(m.tokens_per_second for m in self.metrics) / len(self.metrics)

    @property
    def average_latency_ms(self) -> float:
        return sum(m.first_token_ms for m in self.metrics) / len(self.metrics)

    @property
    def average_power_usage(self) -> Optional[float]:
        powers = [
            m.power_usage_watts for m in self.metrics if m.power_usage_watts is not None
        ]
        return sum(powers) / len(powers) if powers else None
