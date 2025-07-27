"""
MongoDB connection management.

This module provides functions for establishing and closing MongoDB connections.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

# Global variables to store database connection
_client = None
_db = None


def connect_to_mongo():
    """
    Initialize connection to MongoDB.

    This function should be called at the start of the application
    to establish the database connection.
    """
    global _client, _db

    settings = get_settings()

    # Create client if it doesn't exist
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
        _db = _client[settings.mongo_db_name]


def close_mongo_connection():
    """
    Close the MongoDB connection.

    This function should be called when shutting down the application
    to ensure proper cleanup of database resources.
    """
    global _client, _db

    if _client is not None:
        _client.close()
        _client = None
        _db = None


def get_mongo_client():
    """
    Get the current MongoDB client.

    Returns:
        The current AsyncIOMotorClient instance or None if not connected
    """
    return _client


def get_mongo_db():
    """
    Get the current MongoDB database.

    Returns:
        The current AsyncIOMotorDatabase instance or None if not connected
    """
    return _db
