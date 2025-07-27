from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class QA(BaseModel):
    """Question and Answer pair model for user history."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    question: str
    answer: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware (UTC)."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AccessToken(BaseModel):
    """Access token model with expiration."""

    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("expires_at", "created_at")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    def is_valid(self) -> bool:
        """Check if the token is still valid (not expired)."""
        return datetime.now(timezone.utc) < self.expires_at


class User(BaseModel):
    """User model for authorized users."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    email: EmailStr
    name: str
    access_token: AccessToken
    history: List[QA] = Field(default_factory=list, max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("created_at", "updated_at")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    def add_qa(self, question: str, answer: str) -> None:
        """Add a question-answer pair to history, maintaining max 30 items."""
        qa = QA(question=question, answer=answer)
        self.history.append(qa)

        # Keep only the last 30 Q/A pairs
        if len(self.history) > 30:
            self.history = self.history[-30:]

        self.updated_at = datetime.now(timezone.utc)

    def update_token(self, token: str, expires_at: datetime) -> None:
        """Update the user's access token."""
        self.access_token = AccessToken(token=token, expires_at=expires_at)
        self.updated_at = datetime.now(timezone.utc)

    def is_token_valid(self) -> bool:
        """Check if the user's access token is valid."""
        return self.access_token.is_valid()


class UserCreate(BaseModel):
    """Model for creating a new user."""

    email: EmailStr
    name: str
    token: str
    expires_at: datetime

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("expires_at")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure expires_at is timezone-aware (UTC)."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class UserUpdate(BaseModel):
    """Model for updating user information."""

    name: Optional[str] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("expires_at")
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure expires_at is timezone-aware (UTC) if provided."""
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
