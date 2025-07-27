"""
MongoDB implementation of the document repository.
"""

import uuid
from typing import AsyncIterator, Optional, Dict, Any

from app.models import ParsedDocument
from app.db.interfaces import DocRepo
from app.db.mongo.connection import get_mongo_db, connect_to_mongo, get_mongo_client


class MongoDocRepo(DocRepo):
    """MongoDB implementation of the DocRepo interface."""

    def __init__(self):
        """Initialize MongoDB repository without establishing connection."""
        connect_to_mongo()
        self.client = get_mongo_client
        self.db = get_mongo_db()
        self.collection = self.db["docs"]

    def _ensure_connection(self):
        """Ensure database connection is established."""
        if self.db is None:
            self.db = get_mongo_db()
            if self.db is None:
                raise RuntimeError(
                    "MongoDB connection not established. Call connect_to_mongo() first."
                )
            self.collection = self.db["docs"]

    async def upsert(self, doc: ParsedDocument) -> str:
        """
        Insert or replace a document.

        Args:
            doc: The document to insert or update

        Returns:
            The UUID hex ID of the document
        """
        self._ensure_connection()

        # Generate new ID if none exists
        if not doc.id:
            doc.id = uuid.uuid4().hex

        # Convert to dict for storage
        doc_dict = doc.model_dump()

        # Use the id as _id for MongoDB
        doc_dict["_id"] = doc_dict.pop("id")

        # Upsert the document
        await self.collection.replace_one({"_id": doc_dict["_id"]}, doc_dict, upsert=True)

        # Return the document ID
        return doc_dict["_id"]

    async def delete(self, doc_id: str) -> None:
        """
        Hard-delete a document record.

        Args:
            doc_id: The ID of the document to delete
        """
        self._ensure_connection()
        await self.collection.delete_one({"_id": doc_id})

    async def delete_by_path(self, path: str) -> int:
        """
        Hard-delete all documents with the specified path.

        Args:
            path: The file path of documents to delete

        Returns:
            The number of documents deleted
        """
        self._ensure_connection()
        result = await self.collection.delete_many({"path": path})
        return result.deleted_count

    async def get(self, doc_id: str) -> Optional[ParsedDocument]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: The ID of the document to retrieve

        Returns:
            The full document (including text) or None if not found
        """
        self._ensure_connection()
        raw = await self.collection.find_one({"_id": doc_id})

        if not raw:
            return None

        # Convert MongoDB _id to id for ParsedDocument
        raw["id"] = raw.pop("_id")

        # Return parsed document
        return ParsedDocument(**raw)

    async def list_meta(self) -> AsyncIterator[ParsedDocument]:
        """
        Stream metadata-only documents.

        Returns:
            An async iterator yielding documents without text content,
            ordered by uploaded_at DESC
        """
        self._ensure_connection()
        # Find all documents, exclude text, and sort by uploaded_at DESC
        cursor = self.collection.find({}, {"text": 0}).sort("uploaded_at", -1)

        async for raw in cursor:
            # Convert MongoDB _id to id for ParsedDocument
            raw["id"] = raw.pop("_id")

            # Add empty text field since it was excluded but is required by the model
            raw["text"] = ""

            # Yield parsed document
            yield ParsedDocument(**raw)

    async def query(self, topic: str = None, keyword: str = None) -> AsyncIterator[ParsedDocument]:
        """
        Stream documents where topics or keywords match.

        Args:
            topic: Optional topic to filter by
            keyword: Optional keyword to filter by

        Returns:
            An async iterator yielding matching documents

        Raises:
            ValueError: If both topic and keyword are None
        """
        self._ensure_connection()
        # Ensure at least one parameter is provided
        if topic is None and keyword is None:
            raise ValueError("At least one of topic or keyword must be provided")

        # Build query based on provided parameters
        query: Dict[str, Any] = {"$or": []}

        if topic:
            query["$or"].append({"topics": topic})

        if keyword:
            query["$or"].append({"keywords": keyword})

        # Find matching documents, exclude text
        cursor = self.collection.find(query, {"text": 0})

        async for raw in cursor:
            # Convert MongoDB _id to id for ParsedDocument
            raw["id"] = raw.pop("_id")

            # Add empty text field since it was excluded but is required by the model
            raw["text"] = ""

            # Yield parsed document
            yield ParsedDocument(**raw)

    async def exists(self, doc_id: str) -> bool:
        """
        Check if a document with the given ID exists.

        Args:
            doc_id: The ID of the document to check

        Returns:
            True if the document exists, False otherwise
        """
        self._ensure_connection()
        count = await self.collection.count_documents({"_id": doc_id}, limit=1)
        return count > 0

    async def get_id_by_path(self, path: str) -> Optional[str]:
        """
        Get a document's ID by its file path.

        Args:
            path: The full path of the document

        Returns:
            The document ID if found, None otherwise
        """
        self._ensure_connection()
        result = await self.collection.find_one({"path": path}, projection={"_id": 1})
        if result:
            return result["_id"]
        return None

    async def set_summary(self, doc_id: str, length: int, summary: str) -> None:
        """
        Persist a summary for a document.

        Args:
            doc_id: The ID of the document
            length: The length of the summary
            summary: The summary text
        """
        self._ensure_connection()
        # Set field name for summary
        field = f"summaries.{length}"

        # Update document with summary
        await self.collection.update_one({"_id": doc_id}, {"$set": {field: summary}})
