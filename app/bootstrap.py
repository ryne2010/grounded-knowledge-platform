from __future__ import annotations

from pathlib import Path

from .config import settings
from .ingestion import ingest_file
from .storage import connect, init_db, list_docs


def bootstrap_demo_corpus() -> None:
    """Load a small, safe demo corpus if the DB is empty.

    This enables a fully read-only public demo with no uploads.
    """

    if not settings.bootstrap_demo_corpus:
        return

    corpus_dir = Path(settings.demo_corpus_path)
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        return

    # Only bootstrap if DB has no docs.
    try:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            if list_docs(conn):
                return
    except Exception:
        # If DB path is invalid/unwritable, we'll fail later anyway.
        return

    for p in sorted(corpus_dir.glob("**/*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".txt", ".pdf"}:
            continue

        # Use a stable source label so doc_ids are stable across environments.
        ingest_file(p, title=p.stem.replace("_", " "), source=f"demo:{p.name}")
