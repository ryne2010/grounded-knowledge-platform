from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import settings
from .embeddings import HashEmbedder, NoEmbedder, SentenceTransformerEmbedder
from .ocr import extract_text_from_pdf
from .storage import (
    Chunk,
    connect,
    delete_doc_contents,
    init_db,
    insert_chunks,
    insert_embeddings,
    upsert_doc,
)


def _slugify(text: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return t or "doc"


def stable_doc_id(title: str, source: str) -> str:
    """Short stable id derived from title + source."""
    h = hashlib.sha1(f"{title}\n{source}".encode("utf-8")).hexdigest()[:10]
    return f"{_slugify(title)[:32]}-{h}"


def chunk_text(text: str, chunk_size_chars: int, chunk_overlap_chars: int) -> list[str]:
    text = text.replace("\r\n", "\n")
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for p in paras:
        if len(buf) + len(p) + 2 <= chunk_size_chars:
            buf = f"{buf}\n\n{p}".strip()
        else:
            flush()
            # If a single paragraph is huge, hard split it
            while len(p) > chunk_size_chars:
                chunks.append(p[:chunk_size_chars].strip())
                p = p[chunk_size_chars - chunk_overlap_chars :]
            buf = p.strip()

    flush()

    # Add overlap by simple char overlap between adjacent chunks
    if chunk_overlap_chars > 0 and len(chunks) > 1:
        overlapped: list[str] = []
        prev_tail = ""
        for c in chunks:
            if prev_tail:
                overlapped.append((prev_tail + "\n" + c).strip())
            else:
                overlapped.append(c)
            prev_tail = c[-chunk_overlap_chars:]
        return overlapped

    return chunks


@dataclass(frozen=True)
class IngestResult:
    doc_id: str
    num_chunks: int
    embedding_dim: int


def _get_embedder():
    if settings.embeddings_backend == "none":
        return NoEmbedder(1)
    if settings.embeddings_backend == "sentence-transformers":
        return SentenceTransformerEmbedder(settings.embeddings_model)
    return HashEmbedder(settings.embedding_dim)


def ingest_text(*, title: str, source: str, text: str, doc_id: str | None = None) -> IngestResult:
    embedder = _get_embedder()
    doc_id = doc_id or stable_doc_id(title, source)

    chunks = chunk_text(text, settings.chunk_size_chars, settings.chunk_overlap_chars)
    chunk_objs: list[Chunk] = []
    for i, c in enumerate(chunks):
        chunk_id = f"{doc_id}__{i:05d}"
        chunk_objs.append(Chunk(chunk_id=chunk_id, doc_id=doc_id, idx=i, text=c))

    embs = embedder.embed([c.text for c in chunk_objs])  # (n, dim)
    rows = [(chunk.chunk_id, int(embs.shape[1]), vec.astype(np.float32).tobytes()) for chunk, vec in zip(chunk_objs, embs, strict=True)]

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        upsert_doc(conn, doc_id=doc_id, title=title, source=source)
        delete_doc_contents(conn, doc_id)
        insert_chunks(conn, chunk_objs)
        insert_embeddings(conn, rows)
        conn.commit()

    return IngestResult(doc_id=doc_id, num_chunks=len(chunk_objs), embedding_dim=int(embs.shape[1]))


def ingest_file(path: str | Path, *, title: str | None = None, source: str | None = None) -> IngestResult:
    path = Path(path)
    title = title or path.stem
    # Use filename as the default source so doc_ids are stable across machines.
    source = source or path.name

    if path.suffix.lower() in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8")
        return ingest_text(title=title, source=source, text=text)

    if path.suffix.lower() == ".pdf":
        # Robust extraction via PyMuPDF; optionally OCR scanned pages with Tesseract.
        res = extract_text_from_pdf(path)
        if not res.text.strip():
            raise RuntimeError("No text could be extracted from PDF (is it scanned? enable OCR_ENABLED=1).")
        return ingest_text(title=title, source=source, text=res.text)

    raise ValueError(f"Unsupported file type: {path.suffix}. Use .md, .txt, or .pdf")
