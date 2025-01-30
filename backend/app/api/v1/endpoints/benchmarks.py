from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from ....benchmarks.core.benchmark_engine import BenchmarkEngine
from ....benchmarks.schemas.benchmark import (
    BenchmarkConfig,
    BenchmarkResult,
    HardwareSelection,
)
from ....benchmarks.storage.benchmark_storage import BenchmarkStorage
from ....core.deps import get_db
from ....services.ollama import OllamaService
from ....services.prompts import get_prompt_content

router = APIRouter()


@router.post("/start")
async def start_benchmark(
    client_id: str,
    models: List[str],
    hardware: HardwareSelection,
    prompts: Optional[List[str]] = None,
    db: AsyncIOMotorClient = Depends(get_db),
    ollama_service: OllamaService = Depends(),
):
    """Start benchmarks for multiple models."""
    engine = BenchmarkEngine(ollama_service)
    benchmark_ids = []

    # Get prompts content
    if prompts:
        prompt_contents = await get_prompt_content(prompts)
    else:
        # Get all available prompts if none specified
        all_prompts = await get_prompt_content([])
        prompt_contents = {p.id: p.content for p in all_prompts}

    for model in models:
        for _prompt_id, prompt_content in prompt_contents.items():
            config = BenchmarkConfig(
                model_name=model,
                prompt_config={
                    "prompt": prompt_content,
                    "completion_tokens": 100,  # Default value
                },
                hardware=hardware,
            )
            benchmark_id = await engine.start_benchmark(client_id, config)
            benchmark_ids.append(benchmark_id)

    return {"benchmark_ids": benchmark_ids}


@router.get("/status/{benchmark_id}", response_model=Optional[BenchmarkResult])
async def get_benchmark_status(
    benchmark_id: str, db: AsyncIOMotorClient = Depends(get_db)
):
    """Get the status of a running benchmark."""
    storage = BenchmarkStorage(db)
    result = await storage.get_result(benchmark_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return result


@router.get("", response_model=List[BenchmarkResult])
async def get_benchmarks(
    model_name: Optional[str] = None,
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncIOMotorClient = Depends(get_db),
):
    """Get benchmark results with optional filtering."""
    storage = BenchmarkStorage(db)

    if model_name and client_id:
        results = await storage.get_results_for_model_and_client(model_name, client_id)
    elif model_name:
        results = await storage.get_results_for_model(model_name)
    elif client_id:
        results = await storage.get_results_for_client(client_id)
    else:
        results = await storage.get_latest_results(limit)

    if status:
        results = [r for r in results if r.status == status]

    return results[:limit]


@router.delete("/{benchmark_id}")
async def delete_benchmark(benchmark_id: str, db: AsyncIOMotorClient = Depends(get_db)):
    """Delete a specific benchmark result."""
    storage = BenchmarkStorage(db)
    success = await storage.delete_result(benchmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return {"status": "success"}
