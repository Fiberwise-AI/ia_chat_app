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
from typing import Dict, Any, Optional
import asyncio
import json
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
        self._redis_listener_task: Optional[asyncio.Task] = None
        self._redis_client: Optional[object] = None
        self._db_manager: Optional[object] = None

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

    def start_redis_listener(self, redis_client: object, db_manager: object) -> None:
        """
        Start a background task that listens for `pipeline_update` messages.

        Args:
            redis_client: Async Redis client (redis.asyncio.Redis)
            db_manager: DatabaseManager for fetching pipeline JSON
        """
        try:
            if not redis_client:
                return

            self._redis_client = redis_client
            self._db_manager = db_manager
            # Start background listener task
            self._redis_listener_task = asyncio.create_task(self._redis_listener())
            logger.info("Started pipeline_update redis listener")
        except Exception as e:
            logger.error(f"Failed to start redis listener: {e}")

    def stop_redis_listener(self) -> None:
        """Stop the background redis listener task if running."""
        try:
            if self._redis_listener_task and not self._redis_listener_task.done():
                self._redis_listener_task.cancel()
                logger.info("Stopping pipeline_update redis listener")
        except Exception as e:
            logger.error(f"Failed to stop redis listener: {e}")

    async def _redis_listener(self) -> None:
        """Background coroutine that subscribes to 'pipeline_update' and refreshes cache."""
        if not self._redis_client or not self._db_manager:
            return

        try:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe('pipeline_update')
            async for message in pubsub.listen():
                try:
                    # message format from redis.asyncio: dict with keys type/data
                    if not message:
                        continue
                    if message.get('type') != 'message':
                        continue

                    data = message.get('data')
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode('utf-8')
                    if not data:
                        continue

                    payload = json.loads(data)
                    pipeline_name = payload.get('pipeline')
                    if not pipeline_name:
                        continue

                    # Fetch latest JSON from DB and update cache
                    row = self._db_manager.fetch_one(
                        "SELECT pipeline_json FROM pipeline_definitions WHERE name = :name",
                        {"name": pipeline_name}
                    )
                    if row and row.get('pipeline_json'):
                        try:
                            config = json.loads(row['pipeline_json'])
                            self.add(pipeline_name, config)
                            logger.info(f"Pipeline cache refreshed for: {pipeline_name}")
                        except Exception as e:
                            logger.error(f"Failed to parse pipeline JSON for {pipeline_name}: {e}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error processing pipeline update message: {e}")

        except asyncio.CancelledError:
            logger.info("Redis pipeline_update listener cancelled")
        except Exception as e:
            logger.error(f"Redis pipeline_update listener terminated unexpectedly: {e}")
