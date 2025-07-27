from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List
from datetime import datetime
from app.models import ParsedDocument
from app.models.user_models import User, UserCreate, UserUpdate, QA


class DocRepo(ABC):
    """
    Abstract document repository defining operations for document persistence
    """

    @abstractmethod
    async def upsert(self, doc: ParsedDocument) -> str:
        """
        Insert or replace a document.

        Args:
            doc: The document to insert or update

        Returns:
            The UUID hex ID of the document
        """
        pass

    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        """
        Hard-delete a document record.

        Args:
            doc_id: The ID of the document to delete
        """
        pass

    @abstractmethod
    async def delete_by_path(self, path: str) -> int:
        """
        Hard-delete all documents with the specified path.

        Args:
            path: The file path of documents to delete

        Returns:
            The number of documents deleted
        """
        pass

    @abstractmethod
    async def get(self, doc_id: str) -> Optional[ParsedDocument]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: The ID of the document to retrieve

        Returns:
            The full document (including text) or None if not found
        """
        pass

    @abstractmethod
    async def list_meta(self) -> AsyncIterator[ParsedDocument]:
        """
        Stream metadata-only documents.

        Returns:
            An async iterator yielding documents without text content,
            ordered by uploaded_at DESC
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def exists(self, doc_id: str) -> bool:
        """
        Check if a document with the given ID exists.

        Args:
            doc_id: The ID of the document to check

        Returns:
            True if the document exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_id_by_path(self, path: str) -> Optional[str]:
        """
        Get a document's ID by its file path.

        Args:
            path: The full path of the document

        Returns:
            The document ID if found, None otherwise
        """
        pass

    @abstractmethod
    async def set_summary(self, doc_id: str, length: int, summary: str) -> None:
        """
        Persist a summary for a document.

        Args:
            doc_id: The ID of the document
            length: The length of the summary
            summary: The summary text
        """
        pass


class UserRepo(ABC):
    """
    Abstract user repository defining operations for user management
    """

    @abstractmethod
    async def create_user(self, user_data: "UserCreate") -> "User":
        """
        Create a new user.

        Args:
            user_data: The user data for creation

        Returns:
            The created user
        """
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional["User"]:
        """
        Retrieve a user by ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            The user if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional["User"]:
        """
        Retrieve a user by email.

        Args:
            email: The email of the user to retrieve

        Returns:
            The user if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_user_by_token(self, token: str) -> Optional["User"]:
        """
        Retrieve a user by access token.

        Args:
            token: The access token to search for

        Returns:
            The user if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_user(self, user_id: str, user_data: "UserUpdate") -> Optional["User"]:
        """
        Update a user's information.

        Args:
            user_id: The ID of the user to update
            user_data: The updated user data

        Returns:
            The updated user if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_token(
        self, user_id: str, token: str, expires_at: "datetime"
    ) -> Optional["User"]:
        """
        Update a user's access token.

        Args:
            user_id: The ID of the user
            token: The new access token
            expires_at: The token expiration date

        Returns:
            The updated user if found, None otherwise
        """
        pass

    @abstractmethod
    async def add_qa_to_history(self, user_id: str, question: str, answer: str) -> Optional["User"]:
        """
        Add a Q/A pair to a user's history.

        Args:
            user_id: The ID of the user
            question: The question text
            answer: The answer text

        Returns:
            The updated user if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_user_history(self, user_id: str) -> Optional[List["QA"]]:
        """
        Get a user's Q/A history.

        Args:
            user_id: The ID of the user

        Returns:
            The user's history if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: The ID of the user to delete

        Returns:
            True if user was deleted, False if not found
        """
        pass

    @abstractmethod
    async def is_token_valid(self, token: str) -> bool:
        """
        Check if a token is valid (exists and not expired).

        Args:
            token: The token to validate

        Returns:
            True if token is valid, False otherwise
        """
        pass

    @abstractmethod
    async def list_users(self, limit: int = 50, skip: int = 0) -> List["User"]:
        """
        List users with pagination.

        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip

        Returns:
            List of users
        """
        pass
