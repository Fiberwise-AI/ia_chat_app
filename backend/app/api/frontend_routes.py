"""
Frontend routes - Serves the React app with authentication checks.
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import logging

router = APIRouter(tags=["frontend"])
logger = logging.getLogger(__name__)


@router.get("/")
async def serve_frontend(request: Request):
    """
    Serve the frontend app, but redirect to login if not authenticated.

    This ensures users are authenticated before the React app loads,
    preventing the flash of unauthenticated content.
    """
    # Get session manager from app state
    session_manager = request.app.state.session_manager

    # Check if user has valid session
    session_cookie = request.cookies.get("session")

    if not session_cookie:
        logger.info("No session cookie found, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=302)

    # Validate session
    user = await session_manager.validate_session(session_cookie)

    if not user or not user.get("is_active"):
        logger.info(f"Invalid or inactive session, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=302)

    # User is authenticated, redirect to frontend
    # In production, this would serve the built React app
    # In development, the React dev server runs separately
    frontend_port = request.app.state.frontend_port
    return RedirectResponse(url=f"http://localhost:{frontend_port}", status_code=302)


@router.get("/app")
async def app_redirect(request: Request):
    """
    Alternative route for serving the app (same auth check as root).
    """
    return await serve_frontend(request)
