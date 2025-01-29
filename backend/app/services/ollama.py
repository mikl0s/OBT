"""Ollama interaction service."""

import json
from datetime import datetime
from typing import List, Optional

import aiohttp
from fastapi import HTTPException

from app.models.ollama import OllamaModel, OllamaResponse, TestType


async def get_installed_models() -> List[OllamaModel]:
    """Get list of installed Ollama models."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch models from Ollama",
                    )
                data = await response.json()
                return [
                    OllamaModel(
                        name=model["name"],
                        tags=model.get("tags", []),
                        version=model.get("version", "unknown"),
                        size=model.get("size", 0),
                        modified=datetime.fromtimestamp(model.get("modified", 0)),
                    )
                    for model in data.get("models", [])
                ]
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503, detail=f"Failed to connect to Ollama: {str(e)}"
        ) from e


async def generate_completion(
    model: str, prompt: str, stream: bool = True
) -> List[OllamaResponse]:
    """Generate a completion from Ollama."""
    responses: List[OllamaResponse] = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": stream},
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to generate completion",
                    )

                if stream:
                    # Process streaming response
                    async for line in response.content:
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            responses.append(
                                _parse_ollama_response(data, extract_reasoning=True)
                            )
                        except json.JSONDecodeError as e:
                            raise HTTPException(
                                status_code=500,
                                detail=f"Invalid response from Ollama: {str(e)}",
                            ) from e
                else:
                    # Process single response
                    data = await response.json()
                    responses.append(_parse_ollama_response(data, extract_reasoning=True))

        return responses

    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503, detail=f"Failed to connect to Ollama: {str(e)}"
        ) from e


def _parse_ollama_response(data: dict, extract_reasoning: bool = True) -> OllamaResponse:
    """Parse Ollama response and extract reasoning if available."""
    response_text = data.get("response", "")
    reasoning = None

    if extract_reasoning and "<think>" in response_text and "</think>" in response_text:
        # Extract reasoning between <think> tags
        start = response_text.find("<think>") + len("<think>")
        end = response_text.find("</think>")
        if start < end:
            reasoning = response_text[start:end].strip()
            # Remove the think tags and content from the response
            response_text = (
                response_text[:start - len("<think>")] + response_text[end + len("</think>"):]
            ).strip()

    return OllamaResponse(
        response=response_text,
        reasoning=reasoning,
        done=data.get("done", False),
        total_duration=data.get("total_duration", 0),
        load_duration=data.get("load_duration", 0),
        prompt_eval_count=data.get("prompt_eval_count", 0),
        prompt_eval_duration=data.get("prompt_eval_duration", 0),
        eval_count=data.get("eval_count", 0),
        eval_duration=data.get("eval_duration", 0),
    )
