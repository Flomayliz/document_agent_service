from watchdog.observers import Observer
from app.core.config import get_settings
import logging
import asyncio
from pathlib import Path
from .local_handlers import DocumentHandler
from app.ingestion import DocumentWatcher

logger = logging.getLogger(__name__)


class LocalDocumentWatcher(DocumentWatcher):
    """File system watcher for automatic document ingestion."""

    def __init__(self):
        self.observer = Observer()
        self.handler = DocumentHandler()
        self.settings = get_settings()

    async def scan_directory(self, directory: Path):
        """
        Scan a directory and process all existing files.

        Args:
            directory: The directory path to scan
        """
        logger.info(f"Scanning directory for existing files: {directory}")
        try:
            # Use handler's process_directory method to process all files recursively
            await self.handler.process_directory(str(directory))
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

    async def start(self):
        """Start watching the configured folder. Can be called from an async context."""
        watch_path = Path(self.settings.watch_folder)
        watch_path.mkdir(parents=True, exist_ok=True)

        # Set the current event loop in the handler
        loop = asyncio.get_running_loop()
        self.handler.set_loop(loop)

        # Scan directory for existing files before starting the watcher
        await self.scan_directory(watch_path)

        # Start the observer in a non-blocking way
        self.observer.schedule(self.handler, str(watch_path), recursive=True)
        self.observer.start()
        logger.info(f"Started watching folder: {watch_path} (including subdirectories)")

    def stop(self):
        """Stop the file watcher."""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped file watcher")
