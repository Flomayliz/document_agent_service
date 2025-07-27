from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router_agent import router as agent_router
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="LLM Document PoC",
        description="A minimal LLM-Document PoC with LangChain agent",
        version="0.1.0",
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(agent_router, prefix="/agent", tags=["agent"])

    @app.get("/")
    async def root():
        return {"message": "LLM Document PoC API", "version": "0.1.0"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
