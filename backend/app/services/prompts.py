"""Prompt management service."""

import os
from typing import Dict, List

from fastapi import HTTPException
from pydantic import BaseModel


class Prompt(BaseModel):
    id: str
    name: str
    content: str


async def get_available_prompts(prompt_dir: str = "prompts") -> List[Prompt]:
    """Get list of available test prompts."""
    prompts = []
    try:
        for filename in os.listdir(prompt_dir):
            if filename.endswith(".md"):
                prompt_path = os.path.join(prompt_dir, filename)
                with open(prompt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                prompts.append(
                    Prompt(
                        id=os.path.splitext(filename)[0], name=filename, content=content
                    )
                )
        return prompts
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Prompts directory not found: {prompt_dir}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read prompts: {str(e)}"
        ) from e


async def get_prompt_content(
    prompt_ids: List[str], prompt_dir: str = "prompts"
) -> Dict[str, str]:
    """Get content of specific prompts by their IDs."""
    prompts = {}
    try:
        for prompt_id in prompt_ids:
            prompt_path = os.path.join(prompt_dir, f"{prompt_id}.md")
            if not os.path.exists(prompt_path):
                raise HTTPException(
                    status_code=404, detail=f"Prompt not found: {prompt_id}"
                )
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompts[prompt_id] = f.read()
        return prompts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read prompt content: {str(e)}"
        ) from e
