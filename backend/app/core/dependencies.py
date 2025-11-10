"""
Dependency injection for FastAPI routes.

Provides dependency injection functions that extract services from the FastAPI
app state and make them available to route handlers via FastAPI's Depends() system.

These dependencies are used throughout the API routes to access:
- Database manager (nexusql.DatabaseManager)
- LLM service (ia_modules.pipeline.llm_provider_service.LLMProviderService)
- Services registry (ia_modules.pipeline.services.ServiceRegistry)
- Pipeline cache/registry (app.core.pipeline_cache.PipelineCache)

Usage:
    @router.get("/example")
    async def example_route(
        db_manager: DatabaseManager = Depends(get_db_manager),
        llm_service: LLMProviderService = Depends(get_llm_service)
    ):
        # Use injected dependencies
        ...
"""
from fastapi import Request
from ia_modules.pipeline.llm_provider_service import LLMProviderService
from ia_modules.pipeline.services import ServiceRegistry
from nexusql import DatabaseManager
from app.core.container import ServiceContainer
from app.core.pipeline_cache import PipelineCache


def get_services(request: Request) -> ServiceContainer:
    """Get service container from app state."""
    return request.app.state.services


def get_llm_service(request: Request) -> LLMProviderService:
    """Get LLM service from app state."""
    return request.app.state.services.llm_service


def get_services_registry(request: Request) -> ServiceRegistry:
    """Get services registry from app state."""
    return request.app.state.services.services_registry


def get_db_manager(request: Request) -> DatabaseManager:
    """Get database manager from app state."""
    return request.app.state.services.db_manager


def get_pipeline_cache(request: Request) -> PipelineCache:
    """Get pipeline cache from app state."""
    return request.app.state.services.pipeline_cache
