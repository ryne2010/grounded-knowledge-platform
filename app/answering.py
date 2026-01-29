from __future__ import annotations

from .config import settings
from .llm.base import Answer, AnswerProvider
from .llm.extractive import ExtractiveAnswerer


def get_answerer() -> AnswerProvider:
    """
    Returns an AnswerProvider based on env config.
    Falls back to ExtractiveAnswerer if provider cannot be initialized.
    """
    provider = (settings.effective_llm_provider or "extractive").lower().strip()
    if provider == "openai":
        try:
            from .llm.openai_provider import OpenAIAnswerer
            return OpenAIAnswerer()
        except Exception:
            return ExtractiveAnswerer()
    if provider == "gemini":
        try:
            from .llm.gemini_provider import GeminiAnswerer
            return GeminiAnswerer()
        except Exception:
            return ExtractiveAnswerer()
    if provider == "ollama":
        try:
            from .llm.ollama_provider import OllamaAnswerer
            return OllamaAnswerer()
        except Exception:
            return ExtractiveAnswerer()
    return ExtractiveAnswerer()
