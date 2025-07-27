from pathlib import Path
from .base import BaseParser, register
from app.models import ParsedDocument, DocumentMetadata
import hashlib


@register(".txt", ".csv", ".md", ".json")
class TextParser(BaseParser):
    """Parser for plain text files including TXT, CSV, Markdown, and JSON."""

    def parse(self, path: Path) -> ParsedDocument:
        """Extract text and metadata from text-based files."""
        # Attempt to read the file with different encodings
        encodings = ["utf-8", "latin-1", "utf-16"]
        text = None

        for encoding in encodings:
            try:
                text = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            # If all encodings fail, use binary read and decode with errors ignored
            text = path.read_bytes().decode("utf-8", errors="ignore")

        print(f"Parsed {path.name} with {len(text)} characters")

        # Generate content hash ID
        content_hash = hashlib.md5(text.encode()).hexdigest()

        # Determine mime type based on file extension
        suffix = path.suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".md": "text/markdown",
            ".json": "application/json",
        }
        mime = mime_types.get(suffix, "text/plain")

        # Count lines
        lines = text.count("\n") + 1

        # Create document metadata
        document_metadata = DocumentMetadata(
            filename=path.name, size_bytes=path.stat().st_size, mime=mime, lines=lines
        )

        return ParsedDocument(
            id=content_hash,
            filename=path.name,
            path=str(path.absolute()),
            text=text,
            metadata=document_metadata,
        )
