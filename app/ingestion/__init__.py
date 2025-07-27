"""Ingestion module for document processing.

This module provides functionality for watching directories for new files
and processing them through the document ingestion pipeline.
"""

from .watcher import DocumentWatcher
from .parsers import get_parse_registry
from .loader import DocumentLoader, parse_file

__all__ = [
    "DocumentWatcher",
    "get_parse_registry",
    "DocumentLoader",
    "parse_file",
]
