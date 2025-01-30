from unittest.mock import AsyncMock, Mock

import pytest

from ..core.benchmark_engine import BenchmarkEngine
from ..schemas.benchmark import BenchmarkConfig, BenchmarkResult


@pytest.fixture
def mock_ollama_service():
    service = Mock()
    service.generate = AsyncMock()
    return service


@pytest.fixture
def benchmark_engine(mock_ollama_service):
    return BenchmarkEngine(mock_ollama_service)


@pytest.mark.asyncio
async def test_benchmark_initialization(benchmark_engine):
    """Test that benchmark engine initializes correctly."""
    assert benchmark_engine is not None
    assert benchmark_engine.ollama_service is not None
    assert benchmark_engine._running_benchmarks == {}


@pytest.mark.asyncio
async def test_hardware_info_collection(benchmark_engine):
    """Test hardware information collection."""
    hardware_info = benchmark_engine._get_hardware_info()
    assert hardware_info.cpu_cores > 0
    assert hardware_info.cpu_threads > 0
    assert hardware_info.ram_total > 0


@pytest.mark.asyncio
async def test_benchmark_execution(benchmark_engine, mock_ollama_service):
    """Test full benchmark execution."""
    # Setup mock response
    mock_ollama_service.generate.return_value = "Test response " * 100

    config = BenchmarkConfig(
        model_name="test-model",
        prompt_tokens=10,
        completion_tokens=50,
        num_iterations=2,
    )

    result = await benchmark_engine.run_benchmark("test-client", config)

    assert isinstance(result, BenchmarkResult)
    assert result.status == "completed"
    assert len(result.metrics) == 2  # Two iterations
    assert result.client_id == "test-client"
    assert result.config == config
    assert result.error is None


@pytest.mark.asyncio
async def test_failed_benchmark(benchmark_engine, mock_ollama_service):
    """Test benchmark failure handling."""
    mock_ollama_service.generate.side_effect = Exception("Test error")

    config = BenchmarkConfig(
        model_name="test-model",
        prompt_tokens=10,
        completion_tokens=50,
        num_iterations=1,
    )

    result = await benchmark_engine.run_benchmark("test-client", config)

    assert result.status == "failed"
    assert result.error == "Test error"


@pytest.mark.asyncio
async def test_benchmark_metrics(benchmark_engine, mock_ollama_service):
    """Test that metrics are collected correctly."""
    mock_ollama_service.generate.return_value = "Test response"

    config = BenchmarkConfig(
        model_name="test-model",
        prompt_tokens=10,
        completion_tokens=50,
        num_iterations=1,
    )

    result = await benchmark_engine.run_benchmark("test-client", config)

    assert len(result.metrics) == 1
    metrics = result.metrics[0]
    assert metrics.tokens_per_second > 0
    assert metrics.latency_ms > 0
    assert metrics.memory_usage_mb > 0
    assert metrics.cpu_usage_percent >= 0


@pytest.mark.asyncio
async def test_async_benchmark_management(benchmark_engine):
    """Test async benchmark management functions."""
    config = BenchmarkConfig(
        model_name="test-model",
        prompt_tokens=10,
        completion_tokens=50,
        num_iterations=1,
    )

    # Start benchmark
    model_name = await benchmark_engine.start_benchmark("test-client", config)
    assert model_name in benchmark_engine.get_running_benchmarks()

    # Check status
    status = await benchmark_engine.get_benchmark_status(model_name)
    assert status is not None
