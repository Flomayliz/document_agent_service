"""
Factory functions for creating MongoDB repository instances.

This module provides factory functions to create properly configured
repository instances. This approach is better than singletons as it
allows for better testing and dependency injection.
"""

from app.db.mongo.doc_repo import MongoDocRepo
from app.db.mongo.user_repo import MongoUserRepo


def create_doc_repo() -> MongoDocRepo:
    """
    Create a new MongoDB document repository instance.

    Returns:
        A new instance of the MongoDB document repository.
    """
    return MongoDocRepo()


def create_user_repo() -> MongoUserRepo:
    """
    Create a new MongoDB user repository instance.

    Returns:
        A new instance of the MongoDB user repository.
    """
    return MongoUserRepo()
