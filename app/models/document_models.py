from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata model for document information."""

    # Basic file metadata
    filename: str
    size_bytes: int
    mime: str

    # Document-specific metadata
    title: Optional[str] = None
    author: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    pages: Optional[int] = None

    # Format-specific metadata
    lines: Optional[int] = None
    paragraphs: Optional[int] = None
    tables: Optional[int] = None
    creator: Optional[str] = None

    # Additional metadata
    extra: Dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    """Document model returned by parsers representing extracted document information."""

    id: str = ""  # Generated hash ID from content
    filename: str  # Original filename
    path: str  # Full path to the document
    text: str  # Extracted text content
    metadata: DocumentMetadata  # Structured metadata
    keywords: List[str] = Field(default_factory=list)  # Will be filled in later processing
    topics: List[str] = Field(default_factory=list)  # Will be filled in later processing
    summary: Optional[str] = None  # Will be filled in later processing

    # TODO: Review
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
