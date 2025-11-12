"""
WebSocket manager for broadcasting events to connected clients.
Handles pipeline progress updates, URL detection, and document events.
"""

import logging
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections and broadcast events."""

    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Register a new WebSocket connection for a session.

        Args:
            websocket: The WebSocket connection
            session_id: The chat session ID
        """
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {len(self.active_connections[session_id])}")

    async def disconnect(self, websocket: WebSocket, session_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            session_id: The chat session ID
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Clean up empty session sets
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

            logger.info(f"WebSocket disconnected from session {session_id}")

    async def broadcast_to_session(
        self,
        session_id: str,
        event_type: str,
        data: dict
    ):
        """
        Broadcast an event to all connections for a session.

        Args:
            session_id: The chat session ID
            event_type: Type of event (e.g., 'url_detected', 'pipeline_progress')
            data: Event data payload
        """
        if session_id not in self.active_connections:
            logger.debug(f"No active connections for session {session_id}")
            return

        message = {
            'type': event_type,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # Send to all connected clients for this session
        dead_connections = set()

        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        for dead_conn in dead_connections:
            await self.disconnect(dead_conn, session_id)

    async def broadcast_pipeline_event(
        self,
        session_id: str,
        step_name: str,
        status: str,
        message: str,
        metadata: Optional[dict] = None
    ):
        """
        Broadcast a pipeline step progress event.

        Args:
            session_id: The chat session ID
            step_name: Name of the pipeline step
            status: Status of the step ('started', 'completed', 'failed')
            message: Human-readable message
            metadata: Optional additional metadata
        """
        await self.broadcast_to_session(
            session_id=session_id,
            event_type='pipeline_progress',
            data={
                'step': step_name,
                'status': status,
                'message': message,
                'metadata': metadata or {},
                'session_id': session_id  # Include session_id for frontend
            }
        )
        logger.debug(f"Pipeline event broadcast: {step_name} - {status}")

    async def broadcast_url_detected(
        self,
        session_id: str,
        url: str,
        domain: str
    ):
        """
        Broadcast URL detection event.

        Args:
            session_id: The chat session ID
            url: The detected URL
            domain: The domain of the URL
        """
        await self.broadcast_to_session(
            session_id=session_id,
            event_type='url_detected',
            data={
                'url': url,
                'domain': domain,
                'message': f"🔗 Found URL: {url}"
            }
        )
        logger.info(f"URL detected and broadcast: {url}")

    async def broadcast_document_event(
        self,
        session_id: str,
        event_type: str,
        document_id: str,
        filename: str,
        message: str,
        metadata: Optional[dict] = None
    ):
        """
        Broadcast document-related events (upload, processing, etc.).

        Args:
            session_id: The chat session ID
            event_type: Type of document event ('document_uploading', 'document_added', etc.)
            document_id: The document ID
            filename: The document filename
            message: Human-readable message
            metadata: Optional additional metadata
        """
        await self.broadcast_to_session(
            session_id=session_id,
            event_type=event_type,
            data={
                'document_id': document_id,
                'filename': filename,
                'message': message,
                'metadata': metadata or {}
            }
        )
        logger.info(f"Document event broadcast: {event_type} - {filename}")

    def get_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session."""
        return len(self.active_connections.get(session_id, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections across all sessions."""
        return sum(len(conns) for conns in self.active_connections.values())


# Global instance
_websocket_manager = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
