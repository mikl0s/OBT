"""Ollama models and test-related models."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from app.models.base import MongoModel


class OllamaModel(MongoModel):
    """Ollama model information."""

    name: str = Field(..., description="Model name")
    tags: List[str] = Field(default_factory=list, description="Model tags")
    version: str = Field(..., description="Model version")
    size: int = Field(..., description="Model size in bytes")
    modified: datetime = Field(..., description="Last modification date")


class TestType(str, Enum):
    """Test types."""

    COMPLETION = "completion"
    CHAT = "chat"
    EMBEDDING = "embedding"


class TestStatus(str, Enum):
    """Test status."""

    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class ResourceMetrics(MongoModel):
    """Resource usage metrics."""

    timestamp: datetime = Field(..., description="Measurement timestamp")
    ram_usage: float = Field(..., description="RAM usage in MB")
    vram_usage: Optional[float] = Field(None, description="VRAM usage in MB")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    gpu_usage: Optional[float] = Field(None, description="GPU usage percentage")


class OllamaResponse(MongoModel):
    """Individual Ollama response."""

    response: str = Field(..., description="The actual response text")
    reasoning: Optional[str] = Field(None, description="Reasoning/thought process if available")
    done: bool = Field(..., description="Whether this is the final response")
    total_duration: float = Field(..., description="Total processing time in seconds")
    load_duration: float = Field(..., description="Time spent loading the model")
    prompt_eval_count: int = Field(..., description="Number of tokens in the prompt")
    prompt_eval_duration: float = Field(..., description="Time spent processing the prompt")
    eval_count: int = Field(..., description="Number of tokens in the response")
    eval_duration: float = Field(..., description="Time spent generating the response")


class TestMetrics(MongoModel):
    """Test performance metrics."""

    inference_time: float = Field(..., description="Total inference time in seconds")
    tokens_per_second: float = Field(..., description="Tokens processed per second")
    resource_metrics: List[ResourceMetrics] = Field(
        default_factory=list, description="Resource usage over time"
    )


class TestResult(MongoModel):
    """Individual test result."""

    test_type: TestType = Field(..., description="Type of test performed")
    status: TestStatus = Field(..., description="Test status")
    start_time: datetime = Field(..., description="Test start time")
    end_time: Optional[datetime] = Field(None, description="Test end time")
    prompt: str = Field(..., description="Input prompt used for the test")
    responses: List[OllamaResponse] = Field(
        default_factory=list, description="List of responses from Ollama"
    )
    metrics: Optional[TestMetrics] = Field(None, description="Test metrics")
    logs: List[str] = Field(default_factory=list, description="Test logs")
    error: Optional[str] = Field(None, description="Error message if test failed")


class TestSession(MongoModel):
    """Complete test session."""

    hardware_config_id: str = Field(..., description="Reference to hardware configuration")
    status: TestStatus = Field(..., description="Overall session status")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    models: List[Dict[str, List[TestResult]]] = Field(
        ..., description="Test results per model"
    )
    tags: List[str] = Field(default_factory=list, description="Session tags")
