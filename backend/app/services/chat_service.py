"""
Business logic services for chat operations.
"""
from typing import Dict, Any
import logging

from ia_modules.pipeline.graph_pipeline_runner import GraphPipelineRunner
from ia_modules.pipeline.services import ServiceRegistry
from app.core.pipeline_cache import PipelineCache

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat operations."""

    @staticmethod
    async def simple_chat(
        message: str,
        session_id: str,
        services_registry: ServiceRegistry,
        pipeline_cache: PipelineCache
    ) -> Dict[str, Any]:
        """Simple LLM chat using simple pipeline."""
        logger.info(f"Processing chat message: {message[:50]}..." if len(message) > 50 else f"Processing chat message: {message}")
        logger.info(f"Session ID: {session_id}")

        # Get pipeline config from memory cache (no disk I/O)
        pipeline_config = pipeline_cache.get("simple_chat")
        logger.debug(f"Loaded pipeline config: {pipeline_config.get('pipeline_id')}")

        # Run pipeline with session_id (pipeline will fetch history and conditionally generate title)
        logger.info("Executing pipeline...")
        runner = GraphPipelineRunner(services_registry)
        result = await runner.run_pipeline_from_json(
            pipeline_config=pipeline_config,
            input_data={
                "message": message,
                "session_id": session_id
            },
            use_enhanced_features=True
        )

        # Pipeline returns: {"input": {...}, "steps": [...], "output": {...}}
        # The output contains both merged data and step-keyed data
        logger.debug(f"Full pipeline result keys: {result.keys()}")
        output_data = result.get('output', {})
        logger.debug(f"Output data keys: {output_data.keys() if isinstance(output_data, dict) else 'not a dict'}")

        # Try to get response from step ID key first ('chat'), then from merged data
        step_result = output_data.get('chat', output_data)
        logger.debug(f"Step result keys: {step_result.keys() if isinstance(step_result, dict) else 'not a dict'}")

        response_text = step_result.get('response', 'No response generated')
        metadata = step_result.get('metadata', {})

        # Get title if it was generated (from 'generate_title' step)
        title_result = output_data.get('generate_title')
        title = title_result.get('title') if title_result else None

        logger.info(f"Pipeline execution complete. Response length: {len(response_text)}")
        if title:
            logger.info(f"Generated title: {title}")
        logger.debug(f"Pipeline metadata: {metadata}")

        return {
            "response": response_text,
            "metadata": metadata,
            "title": title  # Will be None if not first message
        }
