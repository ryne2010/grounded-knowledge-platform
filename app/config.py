from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Load a local .env for developer convenience.
# - Does NOT override already-set environment variables (CI/Cloud Run wins)
# - Safe: if .env doesn't exist, no-op
load_dotenv: Callable[..., object] | None
try:
    from dotenv import load_dotenv as _load_dotenv  # python-dotenv
except Exception:  # pragma: no cover
    load_dotenv = None
else:
    load_dotenv = _load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]  # repo root (where .env lives)
_ENV_PATH = _REPO_ROOT / ".env"
if load_dotenv is not None and _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH, override=False)


def _env_str(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v.strip() != "" else default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(v.strip())
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return float(v.strip())
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


_ALLOWED_LLM_PROVIDERS = {"extractive", "openai", "gemini", "ollama"}
_ALLOWED_EMBEDDINGS_BACKENDS = {"none", "hash", "sentence-transformers"}


@dataclass(frozen=True)
class Settings:
    """Central configuration for the app.

    Goals:
      - safe by default
      - runnable offline (no external API calls required)
      - configurable via environment variables
      - PUBLIC_DEMO_MODE forces a safety-first config (read-only, no uploads)
    """

    # ---- Safety / demo flags ----
    public_demo_mode: bool
    allow_uploads: bool
    allow_eval: bool

    # Read-only demo bootstrap
    bootstrap_demo_corpus: bool
    demo_corpus_path: str

    # Limits (defense-in-depth for public demos)
    max_question_chars: int
    max_top_k: int

    # Basic in-app rate limiting (helpful for public demos)
    rate_limit_enabled: bool
    rate_limit_window_s: int
    rate_limit_max_requests: int

    # ---- Storage ----
    sqlite_path: str

    # ---- Embeddings ----
    embeddings_backend: str  # none | hash | sentence-transformers
    embeddings_model: str
    embedding_dim: int  # used for hash backend

    # ---- Retrieval ----
    chunk_size_chars: int
    chunk_overlap_chars: int
    top_k_default: int

    # ---- Answering ----
    llm_provider: str  # extractive | openai | gemini | ollama
    max_context_chunks: int

    # OpenAI
    openai_api_key: str | None
    openai_model: str

    # Gemini
    gemini_api_key: str | None
    gemini_model: str

    # Ollama (local open models)
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_s: float

    # ---- OCR ----
    ocr_enabled: bool
    ocr_lang: str
    ocr_max_pages: int
    ocr_dpi: int
    ocr_min_chars: int

    @property
    def effective_llm_provider(self) -> str:
        """Enforce a safety-first config for public demos."""
        if self.public_demo_mode:
            return "extractive"
        return self.llm_provider


def load_settings() -> Settings:
    public_demo_mode = _env_bool("PUBLIC_DEMO_MODE", False)

    # Defaults are developer-friendly. PUBLIC_DEMO_MODE overrides to safe settings.
    allow_uploads = _env_bool("ALLOW_UPLOADS", True)
    allow_eval = _env_bool("ALLOW_EVAL", True)
    bootstrap_demo_corpus = _env_bool("BOOTSTRAP_DEMO_CORPUS", True)
    demo_corpus_path = _env_str("DEMO_CORPUS_PATH", "data/demo_corpus")

    max_question_chars = _env_int("MAX_QUESTION_CHARS", 2000)
    max_top_k = _env_int("MAX_TOP_K", 8)

    rate_limit_enabled = _env_bool("RATE_LIMIT_ENABLED", True)
    rate_limit_window_s = _env_int("RATE_LIMIT_WINDOW_S", 60)
    rate_limit_max_requests = _env_int("RATE_LIMIT_MAX_REQUESTS", 30)

    sqlite_path = _env_str("SQLITE_PATH", "data/index.sqlite")

    embeddings_backend = _env_str("EMBEDDINGS_BACKEND", "hash").lower().strip()
    if embeddings_backend not in _ALLOWED_EMBEDDINGS_BACKENDS:
        embeddings_backend = "hash"

    embeddings_model = _env_str("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    embedding_dim = _env_int("EMBEDDING_DIM", 512)

    chunk_size_chars = _env_int("CHUNK_SIZE_CHARS", 1200)
    chunk_overlap_chars = _env_int("CHUNK_OVERLAP_CHARS", 200)
    top_k_default = _env_int("TOP_K_DEFAULT", 5)

    llm_provider = _env_str("LLM_PROVIDER", "extractive").lower().strip()
    if llm_provider not in _ALLOWED_LLM_PROVIDERS:
        llm_provider = "extractive"

    max_context_chunks = _env_int("MAX_CONTEXT_CHUNKS", 6)

    openai_api_key = os.getenv("OPENAI_API_KEY") or None
    openai_model = _env_str("OPENAI_MODEL", "gpt-4.1-mini")

    gemini_api_key = os.getenv("GEMINI_API_KEY") or None
    gemini_model = _env_str("GEMINI_MODEL", "gemini-2.0-flash")

    ollama_base_url = _env_str("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = _env_str("OLLAMA_MODEL", "llama3.1:8b")
    ollama_timeout_s = _env_float("OLLAMA_TIMEOUT_S", 60.0)

    ocr_enabled = _env_bool("OCR_ENABLED", False)
    ocr_lang = _env_str("OCR_LANG", "eng")
    ocr_max_pages = _env_int("OCR_MAX_PAGES", 10)
    ocr_dpi = _env_int("OCR_DPI", 200)
    ocr_min_chars = _env_int("OCR_MIN_CHARS", 40)

    s = Settings(
        public_demo_mode=public_demo_mode,
        allow_uploads=allow_uploads,
        allow_eval=allow_eval,
        bootstrap_demo_corpus=bootstrap_demo_corpus,
        demo_corpus_path=demo_corpus_path,
        max_question_chars=max_question_chars,
        max_top_k=max_top_k,
        rate_limit_enabled=rate_limit_enabled,
        rate_limit_window_s=rate_limit_window_s,
        rate_limit_max_requests=rate_limit_max_requests,
        sqlite_path=sqlite_path,
        embeddings_backend=embeddings_backend,
        embeddings_model=embeddings_model,
        embedding_dim=embedding_dim,
        chunk_size_chars=chunk_size_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        top_k_default=top_k_default,
        llm_provider=llm_provider,
        max_context_chunks=max_context_chunks,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_timeout_s=ollama_timeout_s,
        ocr_enabled=ocr_enabled,
        ocr_lang=ocr_lang,
        ocr_max_pages=ocr_max_pages,
        ocr_dpi=ocr_dpi,
        ocr_min_chars=ocr_min_chars,
    )

    # Safety-first overrides for public demos.
    if s.public_demo_mode:
        safe_embed = s.embeddings_backend
        if safe_embed not in {"none", "hash", "sentence-transformers"}:
            safe_embed = "hash"

        return Settings(
            public_demo_mode=True,
            allow_uploads=False,
            allow_eval=False,
            bootstrap_demo_corpus=True,
            demo_corpus_path=s.demo_corpus_path,
            max_question_chars=min(s.max_question_chars, 2000),
            max_top_k=min(s.max_top_k, 8),
            rate_limit_enabled=True,
            rate_limit_window_s=s.rate_limit_window_s,
            rate_limit_max_requests=s.rate_limit_max_requests,
            sqlite_path=s.sqlite_path,
            embeddings_backend=safe_embed,
            embeddings_model=s.embeddings_model,
            embedding_dim=s.embedding_dim,
            chunk_size_chars=s.chunk_size_chars,
            chunk_overlap_chars=s.chunk_overlap_chars,
            top_k_default=min(s.top_k_default, 6),
            llm_provider="extractive",
            max_context_chunks=s.max_context_chunks,
            openai_api_key=None,
            openai_model=s.openai_model,
            gemini_api_key=None,
            gemini_model=s.gemini_model,
            ollama_base_url=s.ollama_base_url,
            ollama_model=s.ollama_model,
            ollama_timeout_s=s.ollama_timeout_s,
            ocr_enabled=s.ocr_enabled,
            ocr_lang=s.ocr_lang,
            ocr_max_pages=s.ocr_max_pages,
            ocr_dpi=s.ocr_dpi,
            ocr_min_chars=s.ocr_min_chars,
        )

    return s


settings = load_settings()
