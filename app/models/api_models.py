from pydantic import BaseModel
from typing import Optional


class QARequest(BaseModel):
    """Question answering request model."""

    question: str
    doc_id: Optional[str] = None
    session_id: Optional[str] = None


class QAResponse(BaseModel):
    """Question answering response model."""

    answer: str
    doc_id: Optional[str] = None
    session_id: str


class AgentResponse(BaseModel):
    """Generic agent response model."""

    result: str
    success: bool = True
    message: Optional[str] = None
