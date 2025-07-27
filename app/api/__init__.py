"""
API module containing FastAPI routes and application setup.
"""

# Export the application and create_app function
from app.api.agent_app import app, create_app
from app.api.admin_app import create_admin_app, admin_app

__all__ = ["app", "create_app", "admin_app", "create_admin_app"]
