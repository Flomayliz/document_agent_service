from watchdog.events import FileSystemEventHandler
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from app.db import get_database
from app.agent.llm_backend import get_llm_backend
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List
import os
from pathlib import Path
from app.ingestion.parsers import get_parse_registry
from app.ingestion.loader import parse_file

logger = logging.getLogger(__name__)


class DocumentExtraction(BaseModel):
    """Schema for document extraction results."""

    keywords: List[str] = Field(description="List of key terms/keywords (max 15)")
    topics: List[str] = Field(description="List of main topics/themes (max 10)")
    summary: str = Field(description="Brief summary of the document (150-200 words)")


async def extract_document_info(file_content: str) -> DocumentExtraction:
    """Extract keywords, topics, and summary from a document."""
    # Set up the extraction chain
    parser = PydanticOutputParser(pydantic_object=DocumentExtraction)

    prompt = ChatPromptTemplate.from_template(
        """Analyze the following document and extract:
        1. Keywords: Important terms and concepts (maximum 15)
        2. Topics: Main themes and subjects (maximum 10)
        3. Summary: A concise summary in 150-200 words

        Document content:
        {content}

        {format_instructions}
        """
    )

    # Use common llm utility
    llm = get_llm_backend()
    chain = prompt | llm | parser

    # Process the document
    result = await chain.ainvoke(
        {
            "content": file_content[:8000],  # Limit content length for processing
            "format_instructions": parser.get_format_instructions(),
        }
    )

    return result


class DocumentHandler(FileSystemEventHandler):
    """Handler for file system events in the watch folder."""

    def __init__(self):
        super().__init__()
        # Keep track of the main event loop
        self.loop = None

    def set_loop(self, loop):
        """Set the event loop to use for async operations."""
        self.loop = loop

    def _run_coroutine(self, coro):
        """Run a coroutine safely in the event loop."""
        try:
            if self.loop is None:
                # Try to get the current running loop
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running event loop, we need to run in a new thread
                    logger.warning("No event loop available, running coroutine in new thread")
                    future = asyncio.run_coroutine_threadsafe(coro, asyncio.new_event_loop())
                    return future.result()

            # Use run_coroutine_threadsafe to safely execute in the main loop
            if self.loop and self.loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                # Don't wait for result to avoid blocking the file watcher thread
                return future
            else:
                # Fallback: run directly
                return asyncio.run(coro)
        except Exception as e:
            logger.error(f"Error running coroutine: {e}")
            return None

    def on_created(self, event):
        """Handle file creation events."""
        logger.info(f"Created: {event.src_path}")
        if event.is_directory:
            # When a directory is created, process all files within it
            self._run_coroutine(self.process_directory(event.src_path))
        else:
            # For individual files, process as usual
            self._run_coroutine(self.process_file(event.src_path))

    def on_modified(self, event):
        """Handle file modification events."""
        logger.info(f"Modified: {event.src_path}")
        if not event.is_directory:
            self._run_coroutine(self.process_file(event.src_path, force_update=True))

    def on_deleted(self, event):
        """Handle file deletion events."""
        logger.info(f"Deleted: {event.src_path}")
        if not event.is_directory:
            self._run_coroutine(self.handle_deleted_file(event.src_path))

    def on_moved(self, event):
        """Handle file move events."""
        logger.info(f"Moved from {event.src_path} to {event.dest_path}")
        if event.is_directory:
            # When a directory is moved, process all files in the new location
            self._run_coroutine(self.process_directory(event.dest_path))
        else:
            # For individual files, process as usual
            self._run_coroutine(self.handle_moved_file(event.src_path, event.dest_path))

    async def process_directory(self, dir_path: str):
        """Recursively process all files in a directory."""
        try:
            logger.info(f"Processing directory: {dir_path}")
            
            # Collect all existing file paths in the directory
            existing_file_paths = set()
            for root, _, files in os.walk(dir_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    existing_file_paths.add(file_path)
                    # Process each file individually
                    await self.process_file(file_path)
            
            # After processing all files, clean up database entries for deleted files
            await self._cleanup_deleted_files_in_directory(dir_path, existing_file_paths)
            
        except Exception as e:
            logger.error(f"Error processing directory {dir_path}: {e}")

    async def _cleanup_deleted_files_in_directory(self, dir_path: str, existing_file_paths: set):
        """Remove database entries for files that no longer exist in the directory."""
        try:
            logger.info(f"Cleaning up deleted files in directory: {dir_path}")
            
            db = get_database()
            deleted_count = 0
            
            # Get all documents from the database
            async for doc in db.list_meta():
                # Check if this document is within the processed directory
                if doc.path and doc.path.startswith(dir_path):
                    # If the file no longer exists in the directory, delete it from database
                    if doc.path not in existing_file_paths:
                        logger.info(f"Deleting orphaned document: {doc.id} (path: {doc.path})")
                        await db.delete(doc.id)
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} orphaned documents from directory: {dir_path}")
            else:
                logger.info(f"No orphaned documents found in directory: {dir_path}")
                
        except Exception as e:
            logger.error(f"Error cleaning up deleted files in directory {dir_path}: {e}")

    async def process_file(self, file_path: str, force_update: bool = False):
        """Process a new document file."""
        try:
            db = get_database()
            # Get document ID by original file path
            doc_id = await db.get_id_by_path(file_path)
            if doc_id is not None:
                if force_update:
                    logger.info(f"Force updating existing document: {doc_id}")
                    await db.delete_by_path(file_path)
                else:
                    logger.info(f"Document already exists, skipping: {doc_id}")
                    return

            path = Path(file_path)
            # Use the parser registry to check if file type is supported
            registry = get_parse_registry()
            if path.suffix.lower() not in registry:
                supported_formats = ", ".join(registry.keys())
                logger.info(
                    f"Skipping unsupported file: {file_path} (supported: {supported_formats})"
                )
                return

            logger.info(f"Processing new file: {file_path}")

            # Parse the file content
            document = parse_file(Path(file_path))
            # Extract metadata and content using LLM agent
            doc_info = await extract_document_info(document.text)

            # Update document metadata
            document.keywords = doc_info.keywords
            document.topics = doc_info.topics
            document.summary = doc_info.summary

            # Save to database using DocRepo interface
            doc_id = await db.upsert(document)
            logger.info(f"Document processed successfully: {doc_id}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

    async def handle_deleted_file(self, file_path: str):
        """Handle deletion of a document file by updating the database."""
        try:
            logger.info(f"Handling deleted file: {file_path}")

            # Get the database interface
            db = get_database()

            # Get document ID by file path
            doc_id = await db.get_id_by_path(file_path)

            if doc_id:
                # Delete the document if found
                await db.delete(doc_id)
                logger.info(f"Document with ID {doc_id} deleted successfully")
            else:
                logger.warning(f"No document found for deleted file: {file_path}")

        except Exception as e:
            logger.error(f"Error handling deleted file {file_path}: {e}")

    async def handle_moved_file(self, src_path: str, dest_path: str):
        """Handle moved document file by updating the path in the database."""
        try:
            src_path_obj = Path(src_path)
            dest_path_obj = Path(dest_path)
            src_filename = src_path_obj.name
            dest_filename = dest_path_obj.name

            logger.info(f"Handling moved file from {src_path} to {dest_path}")

            # Get the database interface
            db = get_database()

            # Get document ID by original file path
            doc_id = await db.get_id_by_path(src_path)

            if doc_id:
                # Get the existing document
                doc = await db.get(doc_id)
                if doc:
                    # Update the path and filename if needed
                    doc.path = dest_path
                    if src_filename != dest_filename:
                        doc.filename = dest_filename

                    # Update the document in the database
                    await db.upsert(doc)
                    logger.info(f"Document with ID {doc_id} updated with new path: {dest_path}")
                else:
                    logger.warning(f"Document with ID {doc_id} found but could not be retrieved")
                    await self.process_file(dest_path)
            else:
                # If we couldn't find the document by source path, process it as a new file
                logger.info(
                    f"No document found for source path {src_path}, processing {dest_path} as a new file"
                )
                await self.process_file(dest_path)

        except Exception as e:
            logger.error(f"Error handling moved file from {src_path} to {dest_path}: {e}")
