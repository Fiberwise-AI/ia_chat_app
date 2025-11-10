"""
Service Container - Dependency Injection Container for IA Chat App.
"""
from typing import Optional
from nexusql import DatabaseManager
from ia_modules.pipeline.services import ServiceRegistry
from ia_modules.pipeline.llm_provider_service import LLMProviderService
from app.core.pipeline_cache import PipelineCache


class ServiceContainer:
    """Container holding all application services."""

    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.llm_service: Optional[LLMProviderService] = None
        self.services_registry: Optional[ServiceRegistry] = None
        self.pipeline_cache: Optional[PipelineCache] = None
