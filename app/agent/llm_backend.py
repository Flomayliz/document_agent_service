"""
Common LLM utilities to avoid circular imports.
This module contains shared LLM functionality used across different parts of the application.
"""

from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings


def get_llm_backend():
    """Get the configured LLM backend."""
    settings = get_settings()

    if settings.model_backend == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required but not provided in settings")

        return ChatOpenAI(api_key=settings.openai_api_key, model="gpt-3.5-turbo", temperature=0.1)
    elif settings.model_backend == "ollama":
        return OllamaLLM(model=settings.ollama_model)
    elif settings.model_backend == "gemini":
        # For Gemini, try to use a free tier if API key not provided
        return ChatGoogleGenerativeAI(
            api_key=settings.gemini_api_key, model="gemini-2.0-flash", temperature=0.1
        )
    else:
        raise ValueError(f"Unsupported model backend: {settings.model_backend}")
