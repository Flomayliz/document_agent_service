from pathlib import Path
from pypdf import PdfReader
from .base import BaseParser, register
from app.models import ParsedDocument, DocumentMetadata
import hashlib


@register(".pdf")
class PDFParser(BaseParser):
    """Parser for PDF files using PyPdf."""

    def parse(self, path: Path) -> ParsedDocument:
        """Extract text and metadata from a PDF file."""
        reader = PdfReader(path)
        text = ""

        # Extract text from each page
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"

        # Get number of pages
        num_pages = len(reader.pages)

        # Generate a content hash ID
        content_hash = hashlib.md5(text.encode()).hexdigest()

        # Extract metadata from PDF
        meta = reader.metadata

        # Create document metadata
        document_metadata = DocumentMetadata(
            filename=path.name,
            size_bytes=path.stat().st_size,
            mime="application/pdf",
            title=meta.title if hasattr(meta, "title") and meta.title else None,
            author=meta.author if hasattr(meta, "author") and meta.author else None,
            created=meta.creation_date
            if hasattr(meta, "creation_date") and meta.creation_date
            else None,
            pages=num_pages,
            creator=meta.creator if hasattr(meta, "creator") and meta.creator else None,
        )

        # Create the ParsedDocument
        return ParsedDocument(
            id=content_hash,
            filename=path.name,
            path=str(path.absolute()),
            text=text,
            metadata=document_metadata,
        )
