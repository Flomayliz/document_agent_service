from __future__ import annotations
from langchain.agents import initialize_agent, AgentType
from app.agent.tools import (
    list_docs,
    get_topics,
    get_document,
    document_stats,
    compare_documents,
    search,
    about_leslie,
    get_user_history,
)
from app.agent.llm_backend import get_llm_backend
from functools import lru_cache


@lru_cache()
def get_agent():
    """Get the configured LangChain agent."""
    tools = [
        get_document,
        list_docs,
        get_topics,
        document_stats,
        compare_documents,
        search,
        about_leslie,
        get_user_history,
    ]

    llm = get_llm_backend()

    return initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=30,
        max_execution_time=120,
    )
