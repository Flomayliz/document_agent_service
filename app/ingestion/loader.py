"""
Document loader module for parsing different file types.
Provides both a DocumentLoader class and a convenience parse_file function.
"""

from pathlib import Path
import logging
from .parsers import get_parse_registry
from app.models import ParsedDocument

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Handles loading and parsing of document files using appropriate parser."""

    @staticmethod
    def parse_file(path: Path) -> ParsedDocument:
        """
        Parse a file and return a ParsedDocument object containing text content and metadata.

        Args:
            path: Path to the file to parse

        Returns:
            ParsedDocument object containing extracted text content and metadata

        Raises:
            ValueError: If the file type is not supported
        """
        suffix = path.suffix.lower()

        registry = get_parse_registry()
        if suffix not in registry:
            supported_formats = ", ".join(registry.keys())
            logger.warning(
                f"Unsupported file type: {suffix}. Supported formats: {supported_formats}"
            )
            raise ValueError(f"Unsupported file type: {suffix}")

        logger.info(f"Parsing file {path} using {registry[suffix].__class__.__name__}")
        return registry[suffix].parse(path)


# Convenience function for backward compatibility
def parse_file(path: Path) -> ParsedDocument:
    """
    Parse a file and return a ParsedDocument object.
    This is a convenience function that calls DocumentLoader.parse_file.

    Args:
        path: Path to the file to parse

    Returns:
        ParsedDocument object containing extracted text content and metadata

    Raises:
        ValueError: If the file type is not supported
    """
    return DocumentLoader.parse_file(path)
