"""
MongoDB implementation of the user repository.
"""

from typing import Optional, List
from datetime import datetime, timezone

from app.models.user_models import User, UserCreate, UserUpdate, QA, AccessToken
from app.db.interfaces import UserRepo
from app.db.mongo.connection import get_mongo_db, connect_to_mongo, get_mongo_client


class MongoUserRepo(UserRepo):
    """MongoDB implementation of the UserRepo interface."""

    def __init__(self):
        """Initialize MongoDB repository without establishing connection."""
        connect_to_mongo()
        self.client = get_mongo_client()
        self.db = get_mongo_db()
        self.collection = self.db["users"]

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure a datetime object is timezone-aware (UTC)."""
        if dt.tzinfo is None:
            # If naive, assume it's UTC
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _process_document_datetimes(self, doc: dict) -> dict:
        """Process a MongoDB document to ensure all datetime fields are timezone-aware."""
        datetime_fields = ["created_at", "updated_at"]

        for field in datetime_fields:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = self._ensure_timezone_aware(doc[field])

        # Process access_token datetime fields
        if "access_token" in doc and isinstance(doc["access_token"], dict):
            token_datetime_fields = ["expires_at", "created_at"]
            for field in token_datetime_fields:
                if field in doc["access_token"] and isinstance(
                    doc["access_token"][field], datetime
                ):
                    doc["access_token"][field] = self._ensure_timezone_aware(
                        doc["access_token"][field]
                    )

        # Process history QA timestamps
        if "history" in doc and isinstance(doc["history"], list):
            for qa in doc["history"]:
                if (
                    isinstance(qa, dict)
                    and "timestamp" in qa
                    and isinstance(qa["timestamp"], datetime)
                ):
                    qa["timestamp"] = self._ensure_timezone_aware(qa["timestamp"])

        return doc

    def _ensure_connection(self):
        """Ensure database connection is established."""
        if self.db is None:
            connect_to_mongo()
            self.db = get_mongo_db()
            if self.db is None:
                raise RuntimeError(
                    "MongoDB connection not established. Call connect_to_mongo() first."
                )
            self.collection = self.db["users"]

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: The user data for creation

        Returns:
            The created user
        """
        self._ensure_connection()
        # Create access token
        access_token = AccessToken(token=user_data.token, expires_at=user_data.expires_at)

        # Create user object
        user = User(
            email=user_data.email, name=user_data.name, access_token=access_token, history=[]
        )

        # Convert to dict for storage
        user_dict = user.model_dump()
        user_dict["_id"] = user_dict.pop("id")

        # Insert the user
        await self.collection.insert_one(user_dict)

        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            The user if found, None otherwise
        """
        self._ensure_connection()
        doc = await self.collection.find_one({"_id": user_id})
        if doc:
            doc["id"] = doc.pop("_id")
            doc = self._process_document_datetimes(doc)
            return User(**doc)
        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email.

        Args:
            email: The email of the user to retrieve

        Returns:
            The user if found, None otherwise
        """
        self._ensure_connection()
        doc = await self.collection.find_one({"email": email})
        if doc:
            doc["id"] = doc.pop("_id")
            doc = self._process_document_datetimes(doc)
            return User(**doc)
        return None

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Retrieve a user by access token.

        Args:
            token: The access token to search for

        Returns:
            The user if found, None otherwise
        """
        self._ensure_connection()
        doc = await self.collection.find_one({"access_token.token": token})
        if doc:
            doc["id"] = doc.pop("_id")
            doc = self._process_document_datetimes(doc)
            return User(**doc)
        return None

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """
        Update a user's information.

        Args:
            user_id: The ID of the user to update
            user_data: The updated user data

        Returns:
            The updated user if found, None otherwise
        """
        self._ensure_connection()
        update_dict = {}

        if user_data.name is not None:
            update_dict["name"] = user_data.name

        if user_data.token is not None and user_data.expires_at is not None:
            update_dict["access_token"] = {
                "token": user_data.token,
                "expires_at": user_data.expires_at,
                "created_at": datetime.now(timezone.utc),
            }

        if update_dict:
            update_dict["updated_at"] = datetime.now(timezone.utc)

            result = await self.collection.find_one_and_update(
                {"_id": user_id}, {"$set": update_dict}, return_document=True
            )

            if result:
                result["id"] = result.pop("_id")
                result = self._process_document_datetimes(result)
                return User(**result)

        return None

    async def update_token(self, user_id: str, token: str, expires_at: datetime) -> Optional[User]:
        """
        Update a user's access token.

        Args:
            user_id: The ID of the user
            token: The new access token
            expires_at: The token expiration date

        Returns:
            The updated user if found, None otherwise
        """
        self._ensure_connection()
        update_dict = {
            "access_token": {
                "token": token,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc),
            },
            "updated_at": datetime.now(timezone.utc),
        }

        result = await self.collection.find_one_and_update(
            {"_id": user_id}, {"$set": update_dict}, return_document=True
        )

        if result:
            result["id"] = result.pop("_id")
            result = self._process_document_datetimes(result)
            return User(**result)

        return None

    async def add_qa_to_history(self, user_id: str, question: str, answer: str) -> Optional[User]:
        """
        Add a Q/A pair to a user's history.

        Args:
            user_id: The ID of the user
            question: The question text
            answer: The answer text

        Returns:
            The updated user if found, None otherwise
        """
        self._ensure_connection()
        # Create new QA object
        qa = QA(question=question, answer=answer)

        # Get current user to check history length
        user = await self.get_user(user_id)
        if not user:
            return None

        # Add new QA to history
        new_history = user.history + [qa]

        # Keep only last 30 Q/A pairs
        if len(new_history) > 30:
            new_history = new_history[-30:]

        # Convert history to dict format for storage
        history_dicts = [qa_item.model_dump() for qa_item in new_history]

        # Update the user
        result = await self.collection.find_one_and_update(
            {"_id": user_id},
            {"$set": {"history": history_dicts, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )

        if result:
            result["id"] = result.pop("_id")
            result = self._process_document_datetimes(result)
            return User(**result)

        return None

    async def get_user_history(self, user_id: str) -> Optional[List[QA]]:
        """
        Get a user's Q/A history.

        Args:
            user_id: The ID of the user

        Returns:
            The user's history if found, None otherwise
        """
        user = await self.get_user(user_id)
        if user:
            return user.history
        return None

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: The ID of the user to delete

        Returns:
            True if user was deleted, False if not found
        """
        self._ensure_connection()
        result = await self.collection.delete_one({"_id": user_id})
        return result.deleted_count > 0

    async def is_token_valid(self, token: str) -> bool:
        """
        Check if a token is valid (exists and not expired).

        Args:
            token: The token to validate

        Returns:
            True if token is valid, False otherwise
        """
        user = await self.get_user_by_token(token)
        if user:
            return user.is_token_valid()
        return False

    async def list_users(self, limit: int = 50, skip: int = 0) -> List[User]:
        """
        List users with pagination.

        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip

        Returns:
            List of users
        """
        self._ensure_connection()
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        users = []
        
        async for doc in cursor:
            doc["id"] = doc.pop("_id")
            doc = self._process_document_datetimes(doc)
            users.append(User(**doc))
        
        return users
