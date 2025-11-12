"""
API routes for chat endpoints.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
import json
import logging
from datetime import datetime
from uuid import uuid4

from ia_modules.pipeline.services import ServiceRegistry
from ia_auth_sessions import get_current_active_user
from nexusql import DatabaseManager

from app.models.schemas import ChatMessage, ChatResponse
from app.core.dependencies import get_services_registry, get_pipeline_cache, get_db_manager
from app.services.chat_service import ChatService
from app.core.pipeline_cache import PipelineCache

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    msg: ChatMessage,
    current_user: dict = Depends(get_current_active_user),
    services_registry: ServiceRegistry = Depends(get_services_registry),
    pipeline_cache: PipelineCache = Depends(get_pipeline_cache),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Handle chat message using selected pipeline. Requires authentication."""
    logger.info(f"Chat request from user: {current_user['username']}")

    try:
        # If session_id provided, continue existing chat, otherwise create new
        if msg.session_id:
            session_id = msg.session_id
            # Update session timestamp
            db_manager.execute(
                "UPDATE chat_sessions SET updated_at = :now WHERE id = :id",
                {"id": session_id, "now": datetime.now()}
            )
        else:
            # Create new session with temporary title
            session_id = str(uuid4())
            now = datetime.now()

            # Temporary title - will be updated by pipeline if title is generated
            temp_title = "New Chat"

            db_manager.execute(
                """
                INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                VALUES (:id, :user_id, :title, :created_at, :updated_at)
                """,
                {
                    "id": session_id,
                    "user_id": current_user["id"],
                    "title": temp_title,
                    "created_at": now,
                    "updated_at": now
                }
            )

        # Save user message
        await save_message(db_manager, session_id, "user", msg.message, None)

        # Get AI response (pipeline will fetch history and conditionally generate title)
        result = await ChatService.simple_chat(
            msg.message,
            session_id,
            services_registry,
            pipeline_cache
        )

        # If title was generated, update the session
        if result.get("title"):
            db_manager.execute(
                "UPDATE chat_sessions SET title = :title WHERE id = :id",
                {"title": result["title"], "id": session_id}
            )
            logger.info(f"Updated session {session_id} with generated title: {result['title']}")

        # Save assistant message
        await save_message(
            db_manager,
            session_id,
            "assistant",
            result.get("response", ""),
            result.get("metadata", {})
        )

        return ChatResponse(
            response=result.get("response", ""),
            metadata=result.get("metadata", {}),
            user=current_user["username"],
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all chat sessions for current user."""
    logger.info(f"Fetching sessions for user: {current_user['username']}")

    try:
        sessions = db_manager.fetch_all(
            """
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
            """,
            {"user_id": current_user["id"]}
        )

        return {
            "sessions": [
                {
                    "id": session["id"],
                    "title": session["title"],
                    "created_at": session["created_at"].isoformat(),
                    "updated_at": session["updated_at"].isoformat()
                }
                for session in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    session_id: str = None,
    limit: int = 50
):
    """Get chat history for current user. If session_id not provided, gets most recent session."""
    logger.info(f"Fetching chat history for user: {current_user['username']}")

    try:
        # Get session
        if not session_id:
            session_result = db_manager.fetch_one(
                """
                SELECT id FROM chat_sessions
                WHERE user_id = :user_id
                ORDER BY updated_at DESC LIMIT 1
                """,
                {"user_id": current_user["id"]}
            )
            if not session_result:
                return {"messages": [], "session_id": None}
            session_id = session_result["id"]

        # Get messages
        messages = db_manager.fetch_all(
            """
            SELECT role, content, metadata, created_at
            FROM chat_messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
            LIMIT :limit
            """,
            {"session_id": session_id, "limit": limit}
        )

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "metadata": json.loads(msg["metadata"]) if msg["metadata"] else {},
                    "timestamp": msg["created_at"].isoformat()
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_or_create_session(db_manager: DatabaseManager, user_id: str) -> str:
    """Get or create default chat session for user."""
    # Check for existing session
    result = db_manager.fetch_one(
        "SELECT id FROM chat_sessions WHERE user_id = :user_id ORDER BY updated_at DESC LIMIT 1",
        {"user_id": user_id}
    )

    if result:
        # Update timestamp
        db_manager.execute(
            "UPDATE chat_sessions SET updated_at = :now WHERE id = :id",
            {"id": result["id"], "now": datetime.now()}
        )
        return result["id"]

    # Create new session
    session_id = str(uuid4())
    now = datetime.now()
    db_manager.execute(
        """
        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
        VALUES (:id, :user_id, :title, :created_at, :updated_at)
        """,
        {
            "id": session_id,
            "user_id": user_id,
            "title": "Chat Session",
            "created_at": now,
            "updated_at": now
        }
    )
    return session_id


async def save_message(
    db_manager: DatabaseManager,
    session_id: str,
    role: str,
    content: str,
    metadata: dict
):
    """Save a chat message to database."""
    db_manager.execute(
        """
        INSERT INTO chat_messages (id, session_id, role, content, metadata, created_at)
        VALUES (:id, :session_id, :role, :content, :metadata, :created_at)
        """,
        {
            "id": str(uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata) if metadata else None,
            "created_at": datetime.now()
        }
    )
    logger.debug(f"Saved {role} message to session {session_id}")


@router.get("/pipelines")
async def list_pipelines():
    """List available pipelines."""
    return {
        "pipelines": [
            {
                "id": "simple",
                "name": "Simple Chat",
                "description": "Direct LLM conversation"
            }
        ]
    }


@router.get("/health")
async def health(
    services_registry: ServiceRegistry = Depends(get_services_registry)
):
    """Health check endpoint (public)."""
    llm_service = services_registry.get('llm_provider')

    # Handle both LiteLLMAdapter (returns dict) and LLMProviderService (returns list)
    llm_providers = []
    if llm_service:
        providers = llm_service.list_providers()
        if isinstance(providers, dict):
            # LiteLLMAdapter format
            llm_providers = list(providers.keys())
        elif isinstance(providers, list):
            # LLMProviderService format
            llm_providers = [p['name'] for p in providers]

    return {
        "status": "healthy",
        "llm_providers": llm_providers,
        "auth": "cookie-based sessions"
    }


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat. Requires session cookie."""
    await websocket.accept()

    # Get services from app state
    services_registry = websocket.app.state.services.services_registry
    pipeline_cache = websocket.app.state.services.pipeline_cache
    session_manager = websocket.app.state.session_manager
    db_manager = websocket.app.state.services.db_manager

    # Get WebSocket manager and document processor
    from app.services.websocket_manager import get_websocket_manager
    from app.services.document_processor import DocumentProcessor
    from app.utils.url_extractor import URLExtractor
    import asyncio

    ws_manager = get_websocket_manager()
    doc_processor = DocumentProcessor(db_manager, ws_manager)

    # Validate session from cookie
    session_cookie = websocket.cookies.get("session")
    if not session_cookie:
        await websocket.close(code=1008, reason="Not authenticated")
        return

    user = await session_manager.validate_session(session_cookie)
    if not user or not user.get("is_active"):
        await websocket.close(code=1008, reason="Invalid or inactive session")
        return

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            message = msg_data.get("message", "")
            chat_session_id = msg_data.get("session_id")

            # Handle session creation or continuation
            if chat_session_id:
                session_id = chat_session_id
                db_manager.execute(
                    "UPDATE chat_sessions SET updated_at = :now WHERE id = :id",
                    {"id": session_id, "now": datetime.now()}
                )
            else:
                # Create new session with temporary title
                session_id = str(uuid4())
                now = datetime.now()
                temp_title = "New Chat"

                db_manager.execute(
                    """
                    INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                    VALUES (:id, :user_id, :title, :created_at, :updated_at)
                    """,
                    {
                        "id": session_id,
                        "user_id": user["id"],
                        "title": temp_title,
                        "created_at": now,
                        "updated_at": now
                    }
                )

            # Register this WebSocket connection for the session
            await ws_manager.connect(websocket, session_id)

            # Extract URLs from message
            detected_urls = URLExtractor.extract_urls(message)

            # Process URLs in background if found
            if detected_urls:
                for url_info in detected_urls:
                    if url_info['is_valid'] and not url_info['is_blocked']:
                        # Broadcast URL detection
                        await ws_manager.broadcast_url_detected(
                            session_id=session_id,
                            url=url_info['url'],
                            domain=url_info['domain']
                        )

                        # Process URL in background (don't await)
                        asyncio.create_task(
                            doc_processor.process_url(
                                url=url_info['url'],
                                session_id=session_id,
                                user_id=user['id']
                            )
                        )

            # Save user message
            await save_message(db_manager, session_id, "user", message, None)

            # Send acknowledgment that message was saved
            await websocket.send_json({
                "type": "message_saved",
                "session_id": session_id
            })

            # Get AI response (pipeline will fetch history and conditionally generate title)
            result = await ChatService.simple_chat(
                message,
                session_id,
                services_registry,
                pipeline_cache
            )

            # Update title if generated
            if result.get("title"):
                db_manager.execute(
                    "UPDATE chat_sessions SET title = :title WHERE id = :id",
                    {"title": result["title"], "id": session_id}
                )
                logger.info(f"Updated session {session_id} with generated title: {result['title']}")

            logger.info(f"ChatService result: {result}")

            # Save assistant message
            await save_message(
                db_manager,
                session_id,
                "assistant",
                result.get("response", ""),
                result.get("metadata", {})
            )

            # Send response with session info
            result["user"] = user["username"]
            result["session_id"] = session_id
            result["type"] = "assistant_response"

            logger.info(f"Sending WebSocket response: {result}")

            await websocket.send_json(result)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user['username']}")
        # Disconnect from WebSocket manager if session_id was set
        if 'session_id' in locals():
            await ws_manager.disconnect(websocket, session_id)
