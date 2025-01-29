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

    TEST_A = "test_a"
    TEST_B = "test_b"
    TEST_C = "test_c"


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
    metrics: Optional[TestMetrics] = Field(None, description="Test metrics")
    logs: List[str] = Field(default_factory=list, description="Test logs")
    error: Optional[str] = Field(None, description="Error message if test failed")


class TestSession(MongoModel):
    """Complete test session."""

    hardware_config_id: str = Field(
        ..., description="Reference to hardware configuration"
    )
    status: TestStatus = Field(..., description="Overall session status")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    models: List[Dict[str, List[TestResult]]] = Field(
        ..., description="Test results per model"
    )
    tags: List[str] = Field(default_factory=list, description="Session tags")
