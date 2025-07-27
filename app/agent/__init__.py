"""
Agent module for document processing and Q&A.
"""

from app.agent.agent import get_agent
from app.agent.llm_backend import get_llm_backend

__all__ = [
    "get_agent",
    "get_llm_backend",
]
