"""Benchmark endpoints."""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from ....benchmarks.schemas.benchmark import BenchmarkConfig, BenchmarkResult
from ....benchmarks.storage.benchmark_storage import BenchmarkStorage
from ....core.deps import get_db
from ....services.ollama import get_active_clients
from ....services.prompts import get_prompt_content

router = APIRouter()


@router.post("/start")
async def start_benchmark(
    client_id: str,
    models: List[str],
    hardware: dict,
    prompts: Optional[List[str]] = None,
    db: AsyncIOMotorClient = Depends(get_db),
):
    """Start benchmarks for multiple models."""
    # Verify client is active
    clients = get_active_clients()
    if client_id not in clients:
        raise HTTPException(status_code=404, detail="Client not found or inactive")

    # Get prompts content
    if prompts:
        prompt_contents = await get_prompt_content(prompts)
    else:
        # Get all available prompts if none specified
        all_prompts = await get_prompt_content([])
        prompt_contents = {p.id: p.content for p in all_prompts}

    benchmark_ids = []
    for model in models:
        for prompt_id, prompt_content in prompt_contents.items():
            # Create benchmark configuration
            benchmark_id = str(uuid4())
            config = BenchmarkConfig(
                model_name=model,
                prompt_config={
                    "prompt": prompt_content,
                    "completion_tokens": 100,  # Default value
                },
                hardware=hardware,
            )

            # Store initial benchmark state
            storage = BenchmarkStorage(db)
            await storage.store_result(
                BenchmarkResult(
                    benchmark_id=benchmark_id,
                    client_id=client_id,
                    config=config,
                    status="pending",
                )
            )

            # Send benchmark request to client
            client = clients[client_id]
            await client.run_benchmark(benchmark_id, config)
            benchmark_ids.append(benchmark_id)

    return {"benchmark_ids": benchmark_ids}


@router.post("/update")
async def update_benchmark_result(
    result: BenchmarkResult,
    db: AsyncIOMotorClient = Depends(get_db),
):
    """Update benchmark result from client."""
    storage = BenchmarkStorage(db)
    await storage.store_result(result)
    return {"status": "ok"}


@router.get("/status/{benchmark_id}", response_model=Optional[BenchmarkResult])
async def get_benchmark_status(
    benchmark_id: str,
    db: AsyncIOMotorClient = Depends(get_db),
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
async def delete_benchmark(
    benchmark_id: str,
    db: AsyncIOMotorClient = Depends(get_db),
):
    """Delete a specific benchmark result."""
    storage = BenchmarkStorage(db)
    success = await storage.delete_result(benchmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return {"status": "ok"}
