"""
Fetch Chat History Step - retrieves conversation history from database.
"""
from typing import Dict, Any, List
from ia_modules.pipeline.core import Step
import logging

logger = logging.getLogger(__name__)


class FetchChatHistoryStep(Step):
    """Fetch chat history for a session from the database."""

    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch chat history from database."""
        session_id = data.get('session_id')

        # Get database manager from services
        db_manager = self.services.get('db_manager')

        if not db_manager:
            raise RuntimeError("Database manager not available")

        # If no session_id, this is a new chat
        if not session_id:
            return {
                'chat_history': [],
                'message_count': 0,
                'is_first_message': True
            }

        # Fetch messages for this session
        messages = db_manager.fetch_all(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
            """,
            {"session_id": session_id}
        )

        # Format messages for LLM context
        chat_history = [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]

        # It's the first message if there are no assistant responses yet
        # (user message is saved before pipeline runs, so we check for assistant messages)
        assistant_message_count = sum(1 for msg in messages if msg["role"] == "assistant")
        is_first = assistant_message_count == 0

        logger.info(f"FetchChatHistory: session={session_id}, total_messages={len(messages)}, assistant_count={assistant_message_count}, is_first_message={is_first}")

        return {
            'chat_history': chat_history,
            'message_count': len(messages),
            'is_first_message': is_first
        }
