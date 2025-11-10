"""
Database utilities for IA Chat App.
"""
from pathlib import Path
from nexusql import DatabaseManager
import logging

logger = logging.getLogger(__name__)


async def initialize_chat_schema(db_manager: DatabaseManager) -> bool:
    """
    Initialize chat-specific database schema.

    Creates chat_sessions, chat_messages, and pipeline_executions tables.

    Args:
        db_manager: NexusQL DatabaseManager instance

    Returns:
        True if initialization successful, False otherwise
    """
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = sorted(migrations_dir.glob("V*.sql"))

    if not migration_files:
        logger.warning("No migration files found in database/migrations/")
        return True

    try:
        for migration_file in migration_files:
            logger.info(f"Applying migration: {migration_file.name}")

            with open(migration_file, 'r') as f:
                sql_content = f.read()

            # Execute the entire migration script
            result = await db_manager.execute_script(sql_content)

            if not result.success:
                logger.error(f"Failed to execute migration {migration_file.name}: {result.error}")
                return False

        logger.info(f"Applied {len(migration_files)} chat migration(s)")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize chat schema: {e}")
        return False


async def drop_chat_tables(db_manager: DatabaseManager) -> bool:
    """
    Drop chat tables (for testing/cleanup).

    Args:
        db_manager: NexusQL DatabaseManager instance

    Returns:
        True if successful, False otherwise
    """
    try:
        # Drop in reverse order due to foreign keys
        drop_sql = """
        DROP TABLE IF EXISTS pipeline_executions;
        DROP TABLE IF EXISTS chat_messages;
        DROP TABLE IF EXISTS chat_sessions;
        """
        result = await db_manager.execute_script(drop_sql)

        if not result.success:
            logger.error(f"Failed to drop chat tables: {result.error}")
            return False

        logger.info("Chat tables dropped")
        return True

    except Exception as e:
        logger.error(f"Failed to drop chat tables: {e}")
        return False
