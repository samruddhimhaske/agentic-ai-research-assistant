"""
services/llm_service.py - LLM Factory
=======================================
Ek hi jagah se LLM instance banata hai.

USE_GROQ=False  → OpenAI (gpt-4o-mini)  — needs credits
USE_GROQ=True   → Groq   (llama-3.1-8b) — bilkul FREE
"""

from langchain_openai import ChatOpenAI
from config import settings


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """
    Return the configured LLM instance.
    - USE_GROQ=False → OpenAI gpt-4o-mini
    - USE_GROQ=True  → Groq llama (free, fast)
    """
    if settings.use_groq and settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
        # Groq is OpenAI-API-compatible, so ChatOpenAI works with a custom base_url
        return ChatOpenAI(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            base_url="https://api.groq.com/openai/v1",
            temperature=temperature,
        )
    else:
        # Default: OpenAI
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.model_name,
            temperature=temperature,
        )


def get_active_model_name() -> str:
    """Return which model is currently active (for display)."""
    if settings.use_groq and settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
        return f"Groq / {settings.groq_model}"
    return f"OpenAI / {settings.model_name}"
