"""
Factory for database repository backends.
"""

import os
from app.db.interfaces import DocRepo, UserRepo
from app.db.mongo.factory import (
    create_doc_repo as create_mongo_doc_repo,
    create_user_repo as create_mongo_user_repo,
)


def get_database() -> DocRepo:
    """
    Get an instance of the configured document repository.

    Returns:
        An instance of the configured document repository.

    Raises:
        NotImplementedError: If the configured backend is not supported.
    """
    # Get configured backend from environment variable
    db_backend = os.getenv("DB_BACKEND", "mongo")

    # Select backend based on configuration
    if db_backend == "mongo":
        return create_mongo_doc_repo()
    else:
        raise NotImplementedError(f"Database backend '{db_backend}' is not implemented")


def get_user_database() -> UserRepo:
    """
    Get an instance of the configured user repository.

    Returns:
        An instance of the configured user repository.

    Raises:
        NotImplementedError: If the configured backend is not supported.
    """
    # Get configured backend from environment variable
    db_backend = os.getenv("DB_BACKEND", "mongo")

    # Select backend based on configuration
    if db_backend == "mongo":
        return create_mongo_user_repo()
    else:
        raise NotImplementedError(f"Database backend '{db_backend}' is not implemented")
