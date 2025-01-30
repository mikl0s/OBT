"""Hardware information collection service."""

from typing import Dict, List, Union

from app.models.hardware import GPUInfo, HardwareInfo
from app.services.ollama import get_active_clients, get_client, is_client_healthy


async def get_system_info() -> Union[Dict[str, HardwareInfo], Dict[str, str]]:
    """Get system hardware information from active clients."""
    clients = await get_active_clients()

    if not clients:
        return {"error": "No active clients available"}

    # Return hardware info from all active clients
    client_hardware = {}
    for client in clients:
        if client.get("hardware"):
            client_hardware[client["id"]] = HardwareInfo(**client["hardware"])

    return client_hardware


async def get_available_gpus() -> List[GPUInfo]:
    """Get available GPUs from active clients."""
    clients = await get_active_clients()

    all_gpus = []
    for client in clients:
        if client.get("hardware", {}).get("gpu_count", 0) > 0:
            gpu_info = client["hardware"].get("gpu_info", [])
            for gpu in gpu_info:
                # Add client ID to GPU info for reference
                gpu_data = {**gpu, "client_id": client["id"]}
                all_gpus.append(GPUInfo(**gpu_data))

    return all_gpus


async def update_client_hardware(client_id: str, hardware: HardwareInfo) -> None:
    """Update hardware information for a specific client."""
    if not is_client_healthy(client_id):
        raise ValueError("Client not found or not healthy")

    client = await get_client(client_id)
    if not client:
        raise ValueError("Client not found")

    # Update hardware info
    client["hardware"] = hardware.model_dump()
