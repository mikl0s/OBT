from fastapi import APIRouter, Depends, HTTPException

from ....benchmarks.core.benchmark_engine import BenchmarkEngine
from ....services.ollama import OllamaService

router = APIRouter()


@router.get("/{client_id}/hardware")
async def get_client_hardware(
    client_id: str, ollama_service: OllamaService = Depends()
):
    """Get hardware information for a specific client."""
    if not await ollama_service.is_client_healthy(client_id):
        raise HTTPException(status_code=404, detail="Client not found or not healthy")

    engine = BenchmarkEngine(ollama_service)
    hardware_info = engine._get_hardware_info()

    return hardware_info
