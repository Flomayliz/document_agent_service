"""
User management service providing business logic for user operations.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from app.db.factory import get_user_database
from app.models.user_models import User, UserCreate, UserUpdate, QA


class UserDbHandler:
    """Service class for user management operations."""

    def __init__(self):
        self.repo = get_user_database()

    async def create_user(self, email: str, name: str, token_validity_hours: int = 24) -> User:
        """
        Create a new user with an auto-generated token.

        Args:
            email: User's email address
            name: User's display name
            token_validity_hours: Hours until token expires (default: 24)

        Returns:
            The created user
        """
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=token_validity_hours)

        user_data = UserCreate(email=email, name=name, token=token, expires_at=expires_at)

        return await self.repo.create_user(user_data)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return await self.repo.get_user(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return await self.repo.get_user_by_email(email)

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """Get a user by their access token."""
        return await self.repo.get_user_by_token(token)

    async def authenticate_user(self, token: str) -> Optional[User]:
        """
        Authenticate a user by token and check if it's valid.

        Args:
            token: The access token to validate

        Returns:
            The user if token is valid, None otherwise
        """
        user = await self.repo.get_user_by_token(token)
        if user and user.is_token_valid():
            return user
        return None

    async def refresh_token(self, user_id: str, token_validity_hours: int = 24) -> Optional[User]:
        """
        Generate a new token for a user.

        Args:
            user_id: The user's ID
            token_validity_hours: Hours until new token expires (default: 24)

        Returns:
            The updated user with new token, or None if user not found
        """
        # Generate a new secure token
        new_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=token_validity_hours)

        return await self.repo.update_token(user_id, new_token, expires_at)

    async def update_user_info(self, user_id: str, name: Optional[str] = None) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: The user's ID
            name: New name (optional)

        Returns:
            The updated user, or None if user not found
        """
        user_data = UserUpdate(name=name)
        return await self.repo.update_user(user_id, user_data)

    async def add_qa_to_history(self, user_id: str, question: str, answer: str) -> Optional[User]:
        """
        Add a Q/A pair to user's history.

        Args:
            user_id: The user's ID
            question: The question text
            answer: The answer text

        Returns:
            The updated user with new Q/A in history, or None if user not found
        """
        return await self.repo.add_qa_to_history(user_id, question, answer)

    async def get_user_history(self, user_id: str) -> Optional[List[QA]]:
        """
        Get user's Q/A history.

        Args:
            user_id: The user's ID

        Returns:
            List of Q/A pairs, or None if user not found
        """
        return await self.repo.get_user_history(user_id)

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user account.

        Args:
            user_id: The user's ID

        Returns:
            True if user was deleted, False if not found
        """
        return await self.repo.delete_user(user_id)

    async def is_token_valid(self, token: str) -> bool:
        """
        Check if a token is valid (exists and not expired).

        Args:
            token: The token to validate

        Returns:
            True if token is valid, False otherwise
        """
        return await self.repo.is_token_valid(token)

    async def list_users(self, limit: int = 50, skip: int = 0) -> List[User]:
        """
        List users with pagination.

        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip

        Returns:
            List of users
        """
        return await self.repo.list_users(limit, skip)

    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up users with expired tokens (optional maintenance function).
        This could be implemented as a background task.

        Returns:
            Number of users cleaned up
        """
        # This would require additional repository methods to find expired tokens
        # For now, it's a placeholder for future implementation
        pass


# Create a singleton instance
user_service = UserDbHandler()


def get_user_service() -> UserDbHandler:
    """
    Get the user service instance.

    Returns:
        The user service instance
    """
    return user_service
