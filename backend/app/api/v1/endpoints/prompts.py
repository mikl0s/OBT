from typing import List

from fastapi import APIRouter, HTTPException

from ....services.prompts import (
    TestPrompt,
    TestSuite,
    get_available_test_suites,
    get_test_prompt,
    get_test_suite,
)

router = APIRouter()


@router.get("/test-suites", response_model=List[TestSuite])
async def list_test_suites():
    """Get all available test suites."""
    return await get_available_test_suites()


@router.get("/test-suites/{suite_name}", response_model=TestSuite)
async def get_suite(suite_name: str):
    """Get a specific test suite."""
    suite = await get_test_suite(suite_name)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return suite


@router.get(
    "/test-suites/{suite_name}/prompts/{prompt_name}", response_model=TestPrompt
)
async def get_prompt(suite_name: str, prompt_name: str):
    """Get a specific test prompt from a suite."""
    prompt = await get_test_prompt(suite_name, prompt_name)
    if not prompt:
        raise HTTPException(status_code=404, detail="Test prompt not found")
    return prompt
