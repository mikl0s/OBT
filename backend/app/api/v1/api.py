"""API router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import hardware, models, prompts, tests

api_router = APIRouter()

api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(hardware.router, prefix="/hardware", tags=["hardware"])
api_router.include_router(tests.router, prefix="/tests", tags=["tests"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
