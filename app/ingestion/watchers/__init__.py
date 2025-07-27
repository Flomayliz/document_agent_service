"""
This module provides the document watchers for the ingestion system.
"""

from app.ingestion.watchers.local import LocalDocumentWatcher
from app.ingestion.watchers.factory import create_document_watcher

__all__ = ["LocalDocumentWatcher", "create_document_watcher"]
