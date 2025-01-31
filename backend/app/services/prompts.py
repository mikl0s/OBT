"""Prompt management service."""

import logging
import os
from typing import Dict, List

from fastapi import HTTPException
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)


class Prompt(BaseModel):
    id: str
    name: str
    content: str


class TestPrompt(BaseModel):
    id: str
    name: str
    content: str


class TestSuite(BaseModel):
    name: str
    prompts: List[TestPrompt]


def get_project_root() -> str:
    """Get the project root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    logger.info(f"Project root directory: {root_dir}")
    return root_dir


async def get_available_prompts(prompt_dir: str = "prompts") -> List[Prompt]:
    """Get list of available test prompts."""
    prompts = []
    try:
        root_dir = get_project_root()
        full_prompt_dir = os.path.join(root_dir, prompt_dir)
        logger.info(f"Looking for prompts in: {full_prompt_dir}")

        if not os.path.exists(full_prompt_dir):
            logger.error(f"Prompts directory does not exist: {full_prompt_dir}")
            raise FileNotFoundError(f"Directory not found: {full_prompt_dir}")

        files = os.listdir(full_prompt_dir)
        logger.info(f"Found files in prompts directory: {files}")

        for filename in files:
            if filename.endswith(".md"):
                prompt_path = os.path.join(full_prompt_dir, filename)
                logger.info(f"Reading prompt file: {prompt_path}")
                try:
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    prompt = Prompt(
                        id=os.path.splitext(filename)[0], name=filename, content=content
                    )
                    prompts.append(prompt)
                    logger.info(f"Successfully loaded prompt: {filename}")
                except Exception as e:
                    logger.error(f"Failed to read prompt file {filename}: {str(e)}")
                    raise

        logger.info(f"Successfully loaded {len(prompts)} prompts")
        return prompts
    except FileNotFoundError as e:
        logger.error(f"Prompts directory not found: {full_prompt_dir}")
        raise HTTPException(
            status_code=404, detail=f"Prompts directory not found: {full_prompt_dir}"
        ) from e
    except Exception as e:
        logger.error(f"Failed to read prompts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read prompts: {str(e)}"
        ) from e


async def get_prompt_content(
    prompt_ids: List[str], prompt_dir: str = "prompts"
) -> Dict[str, str]:
    """Get content of specific prompts by their IDs."""
    prompts = {}
    try:
        root_dir = get_project_root()
        full_prompt_dir = os.path.join(root_dir, prompt_dir)
        logger.info(f"Looking for specific prompts in: {full_prompt_dir}")

        for prompt_id in prompt_ids:
            prompt_path = os.path.join(full_prompt_dir, f"{prompt_id}.md")
            logger.info(f"Checking for prompt file: {prompt_path}")

            if not os.path.exists(prompt_path):
                logger.error(f"Prompt file not found: {prompt_path}")
                raise HTTPException(
                    status_code=404, detail=f"Prompt not found: {prompt_id}"
                )

            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    prompts[prompt_id] = f.read()
                logger.info(f"Successfully loaded prompt: {prompt_id}")
            except Exception as e:
                logger.error(f"Failed to read prompt file {prompt_id}: {str(e)}")
                raise

        return prompts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read prompt content: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read prompt content: {str(e)}"
        ) from e


async def get_available_test_suites() -> List[TestSuite]:
    """Get all available test suites."""
    try:
        root_dir = get_project_root()
        prompts_dir = os.path.join(root_dir, "prompts")
        logger.info(f"Looking for prompts in: {prompts_dir}")

        if not os.path.exists(prompts_dir):
            logger.error(f"Prompts directory does not exist: {prompts_dir}")
            raise FileNotFoundError(f"Directory not found: {prompts_dir}")

        files = os.listdir(prompts_dir)
        logger.info(f"Found files in prompts directory: {files}")

        # For now, put all prompts in a single default suite
        prompts = []
        for filename in files:
            if filename.endswith(".md"):
                prompt_path = os.path.join(prompts_dir, filename)
                logger.info(f"Reading prompt file: {prompt_path}")
                try:
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    prompt = TestPrompt(
                        id=os.path.splitext(filename)[0], name=filename, content=content
                    )
                    prompts.append(prompt)
                    logger.info(f"Successfully loaded prompt: {filename}")
                except Exception as e:
                    logger.error(f"Failed to read prompt file {filename}: {str(e)}")
                    raise

        # Create a single test suite with all prompts
        suite = TestSuite(name="default", prompts=prompts)
        logger.info(f"Successfully created test suite with {len(prompts)} prompts")
        return [suite]

    except FileNotFoundError as e:
        logger.error(f"Prompts directory not found: {prompts_dir}")
        raise HTTPException(
            status_code=404, detail=f"Prompts directory not found: {prompts_dir}"
        ) from e
    except Exception as e:
        logger.error(f"Failed to read prompts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read prompts: {str(e)}"
        ) from e


async def get_test_suite(suite_name: str) -> TestSuite:
    """Get a specific test suite."""
    suites = await get_available_test_suites()
    for suite in suites:
        if suite.name == suite_name:
            return suite
    return None


async def get_test_prompt(suite_name: str, prompt_name: str) -> TestPrompt:
    """Get a specific test prompt from a suite."""
    suite = await get_test_suite(suite_name)
    if not suite:
        return None

    for prompt in suite.prompts:
        if prompt.name == prompt_name:
            return prompt
    return None
