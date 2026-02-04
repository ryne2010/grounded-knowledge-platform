from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .config import settings
from .embeddings import Embedder, HashEmbedder, NoEmbedder, SentenceTransformerEmbedder, cosine_sim
from .storage import Chunk, connect, get_embeddings_by_ids, init_db, list_chunks

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

# Simple in-process cache (good enough for a reference implementation).
_CACHE: dict[str, object] = {}
_CACHE_VERSION: int = 0


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    idx: int
    text: str
    score: float
    lexical_score: float
    vector_score: float


_embedder_singleton: Embedder | None = None

def _get_embedder() -> Embedder:
    global _embedder_singleton
    if _embedder_singleton is None:
        backend = settings.embeddings_backend
        if backend == "none":
            _embedder_singleton = NoEmbedder()
        elif backend == "hash":
            _embedder_singleton = HashEmbedder(dim=settings.embedding_dim)
        elif backend == "sentence-transformers":
            _embedder_singleton = SentenceTransformerEmbedder(settings.embeddings_model)
        else:
            # Safety default: avoid network/model downloads.
            _embedder_singleton = HashEmbedder(dim=settings.embedding_dim)
    return _embedder_singleton



def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def invalidate_cache() -> None:
    global _CACHE_VERSION
    _CACHE.clear()
    _CACHE_VERSION += 1


def _load_corpus(conn: sqlite3.Connection) -> tuple[list[Chunk], np.ndarray, list[list[str]]]:
    """
    Returns (chunks, embeddings_matrix, tokenized_chunks).
    embeddings_matrix has shape (n, dim) float32.
    """
    key = f"corpus::{settings.sqlite_path}::{_CACHE_VERSION}"
    cached = _CACHE.get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    chunks = list_chunks(conn)
    chunk_ids = [c.chunk_id for c in chunks]

    # If embeddings are disabled, keep a tiny placeholder matrix and skip loading blobs.
    if settings.embeddings_backend == "none":
        mat = np.zeros((len(chunk_ids), 1), dtype=np.float32)
    else:
        expected_dim = settings.embedding_dim
        emb_rows = get_embeddings_by_ids(conn, chunk_ids)
        if len(emb_rows) != len(chunk_ids):
            mat = np.zeros((len(chunk_ids), expected_dim), dtype=np.float32)
        else:
            dim = int(emb_rows[0][1]) if emb_rows else expected_dim
            mats = []
            for _, _, blob in emb_rows:
                v = np.frombuffer(blob, dtype=np.float32)
                if v.size != dim:
                    v2 = np.zeros((dim,), dtype=np.float32)
                    v2[: min(dim, v.size)] = v[: min(dim, v.size)]
                    v = v2
                mats.append(v)
            mat = np.stack(mats, axis=0).astype(np.float32) if mats else np.zeros((0, dim), dtype=np.float32)

    tokenized = [_tokenize(c.text) for c in chunks]
    _CACHE[key] = (chunks, mat, tokenized)
    return chunks, mat, tokenized


def _lexical_scores_fts(conn: sqlite3.Connection, query: str, limit: int) -> Optional[dict[str, float]]:
    """
    Returns dict chunk_id -> lexical_score in [0,1] (higher is better),
    or None if FTS unavailable.
    """
    try:
        toks = _tokenize(query)
        if not toks:
            return {}
        q = " ".join(toks)
        cur = conn.execute(
            "SELECT chunk_id, bm25(chunks_fts) AS bm FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY bm LIMIT ?",
            (q, limit),
        )
        rows = [(r["chunk_id"], float(r["bm"])) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return None

    if not rows:
        return {}

    bms = np.array([bm for _, bm in rows], dtype=np.float32)
    bms = bms - float(bms.min())
    inv = 1.0 / (1.0 + bms)
    inv = inv / float(inv.max()) if float(inv.max()) > 0 else inv
    return {cid: float(s) for (cid, _), s in zip(rows, inv, strict=True)}


def _lexical_scores_bm25(tokenized_chunks: list[list[str]], query: str) -> dict[int, float]:
    """
    Fallback lexical scorer: BM25 via rank_bm25 over all chunks.
    Returns dict chunk_index -> lexical_score in [0,1].
    """
    try:
        from rank_bm25 import BM25Okapi
    except Exception:
        q = set(_tokenize(query))
        if not q:
            return {}
        scores = {}
        for i, toks in enumerate(tokenized_chunks):
            if not toks:
                continue
            overlap = len(q.intersection(toks)) / (len(q) + 1e-9)
            scores[i] = float(overlap)
        if not scores:
            return {}
        m = max(scores.values())
        return {i: (s / m if m > 0 else s) for i, s in scores.items()}

    bm25 = BM25Okapi(tokenized_chunks)
    q_toks = _tokenize(query)
    if not q_toks:
        return {}
    raw = np.array(bm25.get_scores(q_toks), dtype=np.float32)
    if raw.size == 0:
        return {}
    raw = raw - float(raw.min())
    if float(raw.max()) > 0:
        raw = raw / float(raw.max())
    out: dict[int, float] = {}
    for i, s in enumerate(raw):
        if s > 0:
            out[i] = float(s)
    return out


def retrieve(
    question: str,
    *,
    top_k: int | None = None,
    lexical_limit: int = 40,
    vector_limit: int = 40,
) -> list[RetrievedChunk]:
    """
    Hybrid retrieval:
      - lexical: FTS5 BM25 (preferred) or BM25Okapi fallback
      - vector: cosine similarity
      - combine: average of normalized lexical + vector
    """
    top_k = top_k or settings.top_k_default
    use_vector = settings.embeddings_backend != "none"
    embedder = _get_embedder()

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        chunks, emb_mat, tokenized = _load_corpus(conn)

        if not chunks:
            return []

        # Lexical
        lex_fts = _lexical_scores_fts(conn, question, lexical_limit)
        if lex_fts is not None:
            index_of = {c.chunk_id: i for i, c in enumerate(chunks)}
            lex_scores = {index_of[cid]: s for cid, s in lex_fts.items() if cid in index_of}
        else:
            lex_scores = _lexical_scores_bm25(tokenized, question)

        # Vector (optional)
        if use_vector:
            q_vec = embedder.embed([question]).reshape(-1).astype(np.float32)
            n = float(np.linalg.norm(q_vec))
            if n > 0:
                q_vec = q_vec / n
            sims = cosine_sim(q_vec, emb_mat)
            if sims.size == 0:
                sims = np.zeros((len(chunks),), dtype=np.float32)

            sims = sims - float(sims.min())
            if float(sims.max()) > 0:
                sims = sims / float(sims.max())
        else:
            sims = np.zeros((len(chunks),), dtype=np.float32)

        cand_idx: set[int] = set()
        if lex_scores:
            top_lex = sorted(lex_scores.items(), key=lambda kv: kv[1], reverse=True)[:lexical_limit]
            cand_idx.update(i for i, _ in top_lex)

        if use_vector:
            top_vec_idx = np.argsort(-sims)[:vector_limit].tolist()
            cand_idx.update(int(i) for i in top_vec_idx)

        results: list[RetrievedChunk] = []
        for i in cand_idx:
            c = chunks[i]
            lex_score = float(lex_scores.get(i, 0.0))
            vec_score = float(sims[i])
            score = (0.5 * lex_score + 0.5 * vec_score) if use_vector else lex_score
            results.append(
                RetrievedChunk(
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    idx=c.idx,
                    text=c.text,
                    score=score,
                    lexical_score=lex_score,
                    vector_score=vec_score,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
