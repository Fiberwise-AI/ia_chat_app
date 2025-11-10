"""
Pipeline Loader/Registry - Manages pipeline configurations in memory.

This module provides a centralized registry for pipeline definitions that:
1. Loads pipeline JSON files from disk at application startup
2. Maintains an in-memory registry of all available pipelines
3. Provides fast access to pipeline configurations without repeated file I/O
4. Syncs with database operations (create/update/delete via API)

The term "cache" is somewhat misleading - this is really a pipeline loader and
in-memory registry that serves as the single source of truth for pipeline
configurations during runtime.

Usage in ia_chat_app:
    - Startup (main.py): Loads all *.json files from app/pipelines/
    - Execution (chat_service.py): Retrieves pipeline configs for execution
    - API (pipeline_routes.py): Updates registry when pipelines are modified
"""
import json
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PipelineCache:
    """
    In-memory pipeline registry and loader.

    Loads pipeline JSON definitions from the filesystem at startup and maintains
    them in memory for fast access. Also supports dynamic updates when pipelines
    are created/modified via the API.

    This acts as a pipeline registry rather than a traditional cache - it's the
    primary storage for pipeline configurations during runtime, not just a
    performance optimization layer.

    Attributes:
        _pipelines: Dictionary mapping pipeline names to their JSON configurations
    """

    def __init__(self):
        self._pipelines: Dict[str, Dict[str, Any]] = {}

    def load_all(self, pipelines_dir: Path) -> None:
        """
        Load all pipeline JSON files from a directory into the registry.

        Called at application startup to initialize the pipeline registry with
        all filesystem-based pipeline definitions.

        Args:
            pipelines_dir: Path to directory containing pipeline JSON files
        """
        if not pipelines_dir.exists():
            logger.warning(f"Pipelines directory not found: {pipelines_dir}")
            return

        loaded_count = 0
        for json_file in pipelines_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    config = json.load(f)

                pipeline_name = json_file.stem  # filename without .json
                self._pipelines[pipeline_name] = config
                loaded_count += 1
                logger.info(f"Loaded pipeline: {pipeline_name}")
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Pipeline cache initialized with {loaded_count} pipelines")

    def get(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Get a pipeline configuration by name.

        Used during pipeline execution to retrieve the pipeline definition.

        Args:
            pipeline_name: Name of the pipeline (filename without .json)

        Returns:
            Pipeline configuration dictionary

        Raises:
            KeyError: If pipeline not found in registry
        """
        if pipeline_name not in self._pipelines:
            raise KeyError(f"Pipeline '{pipeline_name}' not found in registry")
        return self._pipelines[pipeline_name]

    def list_pipelines(self) -> list[str]:
        """
        Get list of all available pipeline names.

        Returns:
            List of pipeline names in the registry
        """
        return list(self._pipelines.keys())

    def exists(self, pipeline_name: str) -> bool:
        """
        Check if a pipeline exists in the registry.

        Args:
            pipeline_name: Name of the pipeline to check

        Returns:
            True if pipeline exists, False otherwise
        """
        return pipeline_name in self._pipelines

    def add(self, pipeline_name: str, config: Dict[str, Any]) -> None:
        """
        Add or update a pipeline in the registry.

        Called by the API when pipelines are created or updated via endpoints.
        This keeps the in-memory registry in sync with database operations.

        Args:
            pipeline_name: Name of the pipeline
            config: Pipeline configuration dictionary (JSON structure)
        """
        self._pipelines[pipeline_name] = config
        logger.info(f"Added/updated pipeline in registry: {pipeline_name}")

    def remove(self, pipeline_name: str) -> bool:
        """
        Remove a pipeline from the registry.

        Called by the API when pipelines are deleted via endpoints.

        Args:
            pipeline_name: Name of the pipeline to remove

        Returns:
            True if pipeline was removed, False if not found
        """
        if pipeline_name in self._pipelines:
            del self._pipelines[pipeline_name]
            logger.info(f"Removed pipeline from registry: {pipeline_name}")
            return True
        return False
