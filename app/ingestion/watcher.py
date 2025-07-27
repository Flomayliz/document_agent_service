
import logging
from pathlib import Path
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)



class DocumentWatcher(ABC):
    """Abstract base class for file system watchers for automatic document ingestion."""
    
    @abstractmethod
    async def scan_directory(self, directory: Path):
        """Scan a directory and process all existing files.
        Args:
            directory: The directory path to scan
        """
        pass

    @abstractmethod
    async def start(self):
        """Start watching the configured folder. Can be called from an async context."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop watching the configured folder."""
        pass
