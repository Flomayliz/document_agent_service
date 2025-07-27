#!/usr/bin/env python3
"""
Standalone file watcher script for automatic document ingestion.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.watchers import create_document_watcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WatcherApp:
    """Main application for running the document watcher."""

    def __init__(self):
        self.watcher = None
        self.running = False

    async def start(self):
        """Start the watcher application."""
        logger.info("Starting document watcher...")

        # Start file watcher
        self.watcher = create_document_watcher()
        await self.watcher.start()

        self.running = True
        logger.info("Document watcher started successfully")

        # Keep running until stopped
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the watcher application."""
        logger.info("Stopping document watcher...")

        if self.watcher:
            self.watcher.stop()

        self.running = False
        logger.info("Document watcher stopped")


async def main():
    """Main entry point."""
    app = WatcherApp()

    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        app.running = False

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    await app.start()


if __name__ == "__main__":
    asyncio.run(main())
