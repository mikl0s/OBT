"""Test execution service."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from app.models.ollama import TestResult, TestSession, TestStatus, TestType
from app.services.hardware import get_system_info
from app.services.ollama import generate_completion


async def start_test_session(
    model_names: List[str], prompts: Dict[str, str]
) -> TestSession:
    """Start a new test session."""
    hardware_info = await get_system_info()
    hardware_id = str(hardware_info.id)

    session = TestSession(
        hardware_config_id=hardware_id,
        status=TestStatus.RUNNING,
        start_time=datetime.utcnow(),
        models=[],
        tags=[],
    )

    # Start test execution in background
    asyncio.create_task(run_test_session(session, model_names, prompts))
    return session


async def run_test_session(
    session: TestSession, model_names: List[str], prompts: Dict[str, str]
) -> None:
    """Run tests for all models in the session."""
    try:
        for model_name in model_names:
            model_results = await run_model_tests(model_name, prompts)
            session.models.append({model_name: model_results})

        session.status = TestStatus.COMPLETED
        session.end_time = datetime.utcnow()
    except Exception as e:
        session.status = TestStatus.ERROR
        session.end_time = datetime.utcnow()
        # Log error and update session status in database


async def run_model_tests(model_name: str, prompts: Dict[str, str]) -> List[TestResult]:
    """Run all test types for a specific model."""
    results: List[TestResult] = []

    for prompt_id, prompt_content in prompts.items():
        result = TestResult(
            test_type=TestType.COMPLETION,  # Default to completion for now
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
            prompt=prompt_content,
            responses=[],
        )

        try:
            # Generate completion and collect responses
            responses = await generate_completion(model_name, prompt_content)
            result.responses.extend(responses)
            result.status = TestStatus.COMPLETED
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)

        result.end_time = datetime.utcnow()
        results.append(result)

    return results
