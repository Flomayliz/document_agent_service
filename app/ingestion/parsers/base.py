from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable
from app.models import ParsedDocument

REGISTRY: dict[str, "BaseParser"] = {}  # key = file suffix ".pdf"


def register(*suffixes: str) -> Callable[[type], type]:
    """
    Class decorator: @register(".pdf", ".pdfx")
    Registers cls() singleton in REGISTRY for each suffix.
    """

    def decorator(cls: type) -> type:
        instance = cls()  # one shared instance
        for suf in suffixes:
            REGISTRY[suf.lower()] = instance
        return cls

    return decorator


def get_parse_registry() -> dict[str, "BaseParser"]:
    return REGISTRY


class BaseParser(ABC):
    """Parse a file and return ParsedDocument object."""

    @abstractmethod
    def parse(self, path: Path) -> ParsedDocument:
        """Parse a file and return a ParsedDocument object."""
        ...
