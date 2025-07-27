"""
Factory module for creating document watchers.
TODO: This module should be extended to support different types of watchers.
"""

from app.ingestion.watcher import DocumentWatcher
from app.ingestion.watchers.local.local_watcher import LocalDocumentWatcher


def create_document_watcher() -> DocumentWatcher:
    """Factory function to create a local document watcher."""
    return LocalDocumentWatcher()