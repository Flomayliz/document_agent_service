"""
Database package for document persistence.

This module provides convenience functions for interacting with the document repository.
"""

from app.db.interfaces import DocRepo
from app.db.factory import get_database
from app.db.mongo.connection import connect_to_mongo, close_mongo_connection


# Get repository instance
_repo = get_database()

# Export public helper functions
upsert_doc = _repo.upsert
delete_doc = _repo.delete
fetch_doc = _repo.get
list_docs = _repo.list_meta  # AsyncIterator
query_docs = _repo.query  # AsyncIterator
exists_doc = _repo.exists
get_doc_id_by_path = _repo.get_id_by_path
update_summary = _repo.set_summary


__all__ = [
    "DocRepo",
    "get_database",
    "connect_to_mongo",
    "close_mongo_connection",
    "upsert_doc",
    "delete_doc",
    "fetch_doc",
    "list_docs",
    "query_docs",
    "exists_doc",
    "get_doc_id_by_path",
    "update_summary",
]
