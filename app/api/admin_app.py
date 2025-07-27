"""
Admin API application for user management.

This application runs on a separate port and provides administrative
functionality for user management. It should not be exposed to end users.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router_users import router as users_router
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


def create_admin_app() -> FastAPI:
    """Create and configure the Admin FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Admin API",
        description="Administrative API for user management and system administration",
        version="0.1.0",
        debug=settings.debug,
        docs_url="/admin/docs",  # Custom docs path
        redoc_url="/admin/redoc",  # Custom redoc path
    )

    # Add CORS middleware (more restrictive for admin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8001",
            "http://127.0.0.1:8001",
        ],  # Restrict to admin frontend
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Include admin routers
    app.include_router(users_router, prefix="/admin", tags=["user-management"])

    @app.get("/")
    async def admin_root():
        return {
            "message": "Admin API",
            "version": "0.1.0",
            "documentation": "/admin/docs",
            "endpoints": {"user_management": "/admin/users/", "health_check": "/health"},
        }

    @app.get("/health")
    async def admin_health_check():
        return {
            "status": "healthy",
            "service": "admin-api",
            "endpoints_available": [
                "/admin/users/",
                "/admin/users/me",
                "/admin/users/me/history",
                "/admin/users/me/refresh-token",
                "/admin/users/validate-token",
            ],
        }

    return app


# Create the admin app instance
admin_app = create_admin_app()


if __name__ == "__main__":
    import uvicorn

    # Run the admin server on a different port
    uvicorn.run(
        "app.api.admin_app:admin_app",
        host="127.0.0.1",  # Only bind to localhost for security
        port=8001,  # Different port from main API
        reload=True,
        log_level="info",
    )
