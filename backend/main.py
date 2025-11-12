"""
IA Chat App Backend - FastAPI server with ia_modules pipeline integration.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from datetime import datetime

from nexusql import DatabaseManager
from ia_modules.pipeline.services import ServiceRegistry
from dotenv import load_dotenv

# Import ia_auth_sessions
from ia_auth_sessions import SessionMiddleware, SessionManager, UserManager, html_router, api_router

from app.api.routes import router as chat_router
from app.api.pipeline_routes import router as pipeline_router
from app.api.frontend_routes import router as frontend_router
from app.api.document_routes import router as document_router
from app.core.container import ServiceContainer
from app.core.middleware import RequestLoggingMiddleware
from app.core.pipeline_cache import PipelineCache

# Create logs directory
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging with timestamp-based log file
log_filename = logs_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {log_filename}")

# Load environment variables from project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    logger.warning(".env file not found in project root")

# Get configuration from environment
BACKEND_PORT = int(os.getenv('BACKEND_PORT', '8000'))
FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', '5173'))
AUTH_SECRET_KEY = os.getenv('AUTH_SECRET_KEY', 'dev-secret-key-min-32-chars-long')

# CORS origins - support comma-separated list for production
cors_origins_str = os.getenv('CORS_ORIGINS', f'http://localhost:{FRONTEND_PORT}')
CORS_ORIGINS = [origin.strip() for origin in cors_origins_str.split(',')]


def setup_services(db_manager: DatabaseManager) -> ServiceContainer:
    """Setup all application services."""
    from ia_modules.pipeline.llm_provider_service import LLMProviderService

    services = ServiceContainer()
    services.db_manager = db_manager

    # Setup LLM service using ia_modules (supports 100+ providers via LiteLLM)
    llm_service = LLMProviderService()

    # Register providers with API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')

    if openai_key:
        llm_service.register_provider("openai", model="gpt-4o", api_key=openai_key, is_default=True)
        logger.info("Registered OpenAI provider (gpt-4o)")

    if anthropic_key:
        llm_service.register_provider("anthropic", model="claude-sonnet-4-5-20250929", api_key=anthropic_key)
        logger.info("Registered Anthropic provider (claude-sonnet-4-5)")

    if google_key:
        llm_service.register_provider("google", model="gemini/gemini-2.0-flash-exp", api_key=google_key)
        logger.info("Registered Google provider (gemini-2.0-flash)")

    providers_count = len(llm_service.list_providers())
    logger.info(f"LLM service initialized with {providers_count} provider(s)")

    services.llm_service = llm_service

    # Setup services registry
    services_registry = ServiceRegistry()
    services_registry.register('llm_provider', llm_service)
    services_registry.register('db_manager', db_manager)
    services.services_registry = services_registry

    return services


async def auto_import_pipelines_to_db(db_manager: DatabaseManager, pipeline_cache: PipelineCache, pipelines_dir: Path):
    """
    Auto-import filesystem pipelines to database at startup.

    This ensures pipelines loaded from filesystem are available in the Pipeline Management UI.
    Only imports pipelines that don't already exist in the database.
    """
    import json
    from uuid import uuid4
    from datetime import datetime

    if not pipelines_dir.exists():
        return

    imported_count = 0
    skipped_count = 0

    for json_file in pipelines_dir.glob("*.json"):
        try:
            pipeline_name = json_file.stem

            # Check if pipeline already exists in database
            existing = db_manager.fetch_one(
                "SELECT id FROM pipeline_definitions WHERE name = :name",
                {"name": pipeline_name}
            )

            if existing:
                skipped_count += 1
                continue

            # Get pipeline config from cache (already loaded)
            pipeline_json = pipeline_cache.get(pipeline_name)

            # Insert into database
            pipeline_id = str(uuid4())
            now = datetime.now()

            db_manager.execute(
                """
                INSERT INTO pipeline_definitions
                (id, name, display_name, description, version, pipeline_json, is_active, is_system, created_by, created_at, updated_at)
                VALUES (:id, :name, :display_name, :description, :version, :pipeline_json, :is_active, :is_system, :created_by, :created_at, :updated_at)
                """,
                {
                    "id": pipeline_id,
                    "name": pipeline_name,
                    "display_name": pipeline_json.get("name", pipeline_name),
                    "description": pipeline_json.get("description", ""),
                    "version": pipeline_json.get("version", "1.0.0"),
                    "pipeline_json": json.dumps(pipeline_json),
                    "is_active": True,
                    "is_system": True,  # Filesystem pipelines are system pipelines
                    "created_by": None,  # System pipelines have no creator user
                    "created_at": now,
                    "updated_at": now
                }
            )

            imported_count += 1
            logger.info(f"Auto-imported pipeline to database: {pipeline_name}")

        except Exception as e:
            logger.error(f"Failed to auto-import pipeline {json_file.name}: {e}")

    if imported_count > 0:
        logger.info(f"Auto-imported {imported_count} filesystem pipeline(s) to database")
    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} pipeline(s) (already in database)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    logger.info("=" * 60)
    logger.info("Starting IA Chat App backend...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Backend Port: {BACKEND_PORT}")
    logger.info(f"CORS Origins: {CORS_ORIGINS}")
    logger.info("=" * 60)

    # Initialize database
    db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/ia_chat_app')
    logger.info(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}")  # Hide credentials
    db_manager = DatabaseManager(db_url)

    # Initialize database connection and run migrations
    if not await db_manager.initialize():
        logger.error(f"Database initialization failed for: {db_url}")
        raise RuntimeError(f"Database initialization failed. Check DATABASE_URL in .env: {db_url}")
    logger.info(f"Database connected ({db_manager.config.database_type.value})")

    # Initialize auth tables (users, sessions)
    from ia_auth_sessions import initialize_database
    if not await initialize_database(db_manager):
        raise RuntimeError("Failed to initialize auth database schema")
    logger.info("Auth schema initialized (users, sessions)")

    # Initialize app-specific tables (chat_sessions, chat_messages, pipeline_executions)
    from app.database import initialize_chat_schema
    if not await initialize_chat_schema(db_manager):
        raise RuntimeError("Failed to initialize chat database schema")
    logger.info("Chat schema initialized (chat_sessions, chat_messages, pipeline_executions)")

    # Setup services
    services = setup_services(db_manager)

    # Load pipelines into memory
    pipeline_cache = PipelineCache()
    pipelines_dir = Path(__file__).parent / "app" / "pipelines"
    pipeline_cache.load_all(pipelines_dir)
    services.pipeline_cache = pipeline_cache

    # Auto-import filesystem pipelines to database at startup
    await auto_import_pipelines_to_db(db_manager, pipeline_cache, pipelines_dir)

    # Setup authentication managers
    session_manager = SessionManager(
        db_manager=db_manager,
        secret_key=AUTH_SECRET_KEY,
        max_age=int(os.getenv('AUTH_SESSION_MAX_AGE', '604800'))  # 7 days default
    )
    user_manager = UserManager(db_manager)

    # Store in app.state for dependency injection
    app.state.services = services
    app.state.db_manager = db_manager
    app.state.session_manager = session_manager
    app.state.user_manager = user_manager
    app.state.frontend_port = FRONTEND_PORT

    logger.info("Services initialized")
    llm_providers_list = [p['name'] for p in services.llm_service.list_providers()]
    logger.info(f"LLM service: ia_modules LLMProviderService with {len(llm_providers_list)} provider(s): {llm_providers_list}")
    logger.info(f"Pipelines loaded: {pipeline_cache.list_pipelines()}")
    logger.info("Authentication system ready (cookie-based sessions)")
    logger.info("=" * 60)
    logger.info("Application startup complete!")
    logger.info("=" * 60)

    yield

    # Shutdown - cleanup resources
    logger.info("=" * 60)
    logger.info("Shutting down application...")
    try:
        if db_manager:
            db_manager.disconnect()
            logger.info("Database connection closed")
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info("=" * 60)


app = FastAPI(title="IA Chat App API", lifespan=lifespan)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)

# Add session middleware from ia_auth_sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=AUTH_SECRET_KEY,
    db_manager=None,  # Will be retrieved from app.state in middleware
    session_cookie_name=os.getenv('AUTH_SESSION_COOKIE_NAME', 'session'),
    max_age=int(os.getenv('AUTH_SESSION_MAX_AGE', '604800')),
    cookie_secure=os.getenv('AUTH_COOKIE_SECURE', 'false').lower() == 'true',
    cookie_httponly=os.getenv('AUTH_COOKIE_HTTPONLY', 'true').lower() == 'true',
    cookie_samesite=os.getenv('AUTH_COOKIE_SAMESITE', 'lax')
)

# CORS middleware - support multiple origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # From CORS_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set app name for templates
app.state.app_name = "IA Chat App"

# Include routers
app.include_router(frontend_router)  # Root route with auth check (must be first!)
app.include_router(html_router)  # HTML pages (login, register)
app.include_router(api_router)   # API endpoints (JSON)
app.include_router(chat_router)
app.include_router(pipeline_router)  # Pipeline management
app.include_router(document_router)  # Document upload and scraping


if __name__ == "__main__":
    import uvicorn

    print(f"\n{'='*50}")
    print(f"Backend starting on: http://localhost:{BACKEND_PORT}")
    print(f"Environment: {'production' if os.getenv('ENVIRONMENT') == 'production' else 'development'}")
    print(f"Authentication: Cookie-based sessions (ia_auth_sessions)")
    print(f"{'='*50}\n")

    # Note: reload disabled on Windows due to multiprocessing issues with editable installs
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=BACKEND_PORT,
        log_level="info"
    )
