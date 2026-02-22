from __future__ import annotations

import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional

import numpy as np

from .config import settings
from .embeddings import Embedder, HashEmbedder, NoEmbedder, SentenceTransformerEmbedder, cosine_sim
from .index_maintenance import ensure_index_compatible
from .maintenance import retention_is_expired
from .storage import Chunk, connect, get_chunks_by_ids, get_embeddings_by_ids, init_db, list_chunks
from .tenant import current_tenant_id

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _vec_to_pgvector_literal(vec: np.ndarray) -> str:
    """Convert a 1D numpy vector to pgvector text format: "[1,2,3]"."""
    v = vec.astype(np.float32).reshape(-1)
    n = float(np.linalg.norm(v))
    if n > 0:
        v = v / n
    vals = v.tolist()
    return "[" + ",".join(str(float(x)) for x in vals) + "]"


logger = logging.getLogger(__name__)

# Simple in-process cache (good enough for a reference implementation).
_CACHE: dict[str, object] = {}
_CACHE_VERSION: int = 0
_CACHE_LOCK = Lock()


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    idx: int
    text: str
    score: float
    lexical_score: float
    vector_score: float


def effective_hybrid_weights(*, use_vector: bool) -> tuple[float, float]:
    """Return normalized lexical/vector weights for hybrid retrieval."""
    if not use_vector:
        return (1.0, 0.0)

    lexical = max(0.0, float(settings.retrieval_lexical_weight))
    vector = max(0.0, float(settings.retrieval_vector_weight))
    total = lexical + vector
    if total <= 0:
        return (0.5, 0.5)
    return (lexical / total, vector / total)


def _retrieval_sort_key(item: RetrievedChunk) -> tuple[float, float, float, str, int, str]:
    """Deterministic ordering for ties on floating scores."""
    return (-item.score, -item.lexical_score, -item.vector_score, item.doc_id, int(item.idx), item.chunk_id)


def _log_retrieval_diagnostics(
    *,
    backend: str,
    top_k: int,
    lexical_limit: int,
    vector_limit: int,
    lexical_weight: float,
    vector_weight: float,
    lexical_candidates: int,
    vector_candidates: int,
    merged_candidates: int,
    lexical_ms: float,
    vector_ms: float,
    merge_ms: float,
) -> None:
    if not settings.retrieval_debug_stats:
        return

    logger.info(
        (
            "retrieval.hybrid.stats backend=%s top_k=%d lexical_limit=%d vector_limit=%d "
            "lexical_weight=%.3f vector_weight=%.3f lexical_candidates=%d vector_candidates=%d "
            "merged_candidates=%d lexical_ms=%.2f vector_ms=%.2f merge_ms=%.2f"
        ),
        backend,
        int(top_k),
        int(lexical_limit),
        int(vector_limit),
        float(lexical_weight),
        float(vector_weight),
        int(lexical_candidates),
        int(vector_candidates),
        int(merged_candidates),
        float(lexical_ms),
        float(vector_ms),
        float(merge_ms),
    )


_embedder_singleton: Embedder | None = None
_embedder_lock = Lock()


def _get_embedder() -> Embedder:
    global _embedder_singleton
    if _embedder_singleton is not None:
        return _embedder_singleton

    with _embedder_lock:
        if _embedder_singleton is not None:
            return _embedder_singleton

        backend = settings.embeddings_backend
        try:
            if backend == "none":
                _embedder_singleton = NoEmbedder()
            elif backend == "hash":
                _embedder_singleton = HashEmbedder(dim=settings.embedding_dim)
            elif backend == "sentence-transformers":
                _embedder_singleton = SentenceTransformerEmbedder(settings.embeddings_model)
            else:
                _embedder_singleton = HashEmbedder(dim=settings.embedding_dim)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to initialize embedder backend=%s; falling back to hash. error=%s", backend, e)
            _embedder_singleton = HashEmbedder(dim=settings.embedding_dim)

        return _embedder_singleton


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _is_postgres_conn(conn: Any) -> bool:
    return "psycopg" in type(conn).__module__


def _ph(conn: Any) -> str:
    return "%s" if _is_postgres_conn(conn) else "?"


def _expired_doc_ids_for_doc_ids(conn: Any, doc_ids: set[str], *, now: int) -> set[str]:
    """Return doc_ids that are retention-expired at `now`."""
    if not doc_ids:
        return set()

    ordered_ids = sorted(doc_ids)
    placeholders = ",".join([_ph(conn)] * len(ordered_ids))
    tenant_id = current_tenant_id()
    cur = conn.execute(
        f"SELECT doc_id, retention, updated_at FROM docs WHERE doc_id IN ({placeholders}) AND tenant_id={_ph(conn)}",
        tuple(ordered_ids) + (tenant_id,),
    )

    expired: set[str] = set()
    for row in cur.fetchall():
        doc_id = str(row["doc_id"])
        retention = str(row["retention"])
        updated_at = int(row["updated_at"])
        if retention_is_expired(retention, updated_at=updated_at, now=now):
            expired.add(doc_id)
    return expired


def invalidate_cache() -> None:
    global _CACHE_VERSION
    with _CACHE_LOCK:
        _CACHE.clear()
        _CACHE_VERSION += 1


def _load_corpus(conn: sqlite3.Connection) -> tuple[list[Chunk], np.ndarray, list[list[str]]]:
    """Returns (chunks, embeddings_matrix, tokenized_chunks).

    embeddings_matrix has shape (n, dim) float32.
    """

    key = "::".join(
        [
            "corpus",
            current_tenant_id(),
            settings.sqlite_path,
            settings.embeddings_backend,
            settings.embeddings_model,
            str(settings.embedding_dim),
            str(_CACHE_VERSION),
        ]
    )

    with _CACHE_LOCK:
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

    with _CACHE_LOCK:
        _CACHE[key] = (chunks, mat, tokenized)

    return chunks, mat, tokenized


def _lexical_scores_fts(conn: sqlite3.Connection, query: str, limit: int) -> Optional[dict[str, float]]:
    """Returns dict chunk_id -> lexical_score in [0,1] (higher is better),

    or None if FTS unavailable.
    """

    try:
        toks = _tokenize(query)
        if not toks:
            return {}
        q = " ".join(toks)
        tenant_id = current_tenant_id()
        cur = conn.execute(
            """
            SELECT chunks_fts.chunk_id, bm25(chunks_fts) AS bm
            FROM chunks_fts
            JOIN chunks c ON chunks_fts.chunk_id = c.chunk_id
            WHERE chunks_fts MATCH ? AND c.tenant_id = ?
            ORDER BY bm
            LIMIT ?
            """,
            (q, tenant_id, limit),
        )
        rows = [(r["chunk_id"], float(r["bm"])) for r in cur.fetchall()]
    except Exception:
        return None

    if not rows:
        return {}

    bms = np.array([bm for _, bm in rows], dtype=np.float32)
    bms = bms - float(bms.min())
    inv = 1.0 / (1.0 + bms)
    inv = inv / float(inv.max()) if float(inv.max()) > 0 else inv
    return {cid: float(s) for (cid, _), s in zip(rows, inv, strict=True)}




def _pg_lexical_scores(conn: Any, query: str, limit: int) -> dict[str, float]:
    """Postgres lexical retrieval using built-in full-text search.

    Returns dict chunk_id -> normalized score in [0, 1].
    """

    toks = _tokenize(query)
    if not toks:
        return {}
    q = " ".join(toks)
    limit = max(1, min(int(limit), 2000))

    tenant_id = current_tenant_id()
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH q AS (SELECT plainto_tsquery('english', %s) AS query)
            SELECT c.chunk_id, ts_rank_cd(to_tsvector('english', c.text), q.query) AS score
            FROM chunks c, q
            WHERE to_tsvector('english', c.text) @@ q.query
              AND c.tenant_id = %s
            ORDER BY score DESC
            LIMIT %s
            """,
            (q, tenant_id, limit),
        )
        rows = cur.fetchall()

    scores = {str(r["chunk_id"]): float(r["score"]) for r in rows if r.get("chunk_id") is not None}
    if not scores:
        return {}

    mx = max(scores.values())
    if mx > 0:
        scores = {cid: (s / mx) for cid, s in scores.items()}
    return scores


def _pg_vector_scores(conn: Any, query: str, embedder: Embedder, limit: int) -> dict[str, float]:
    """Postgres vector retrieval using pgvector cosine distance.

    Returns dict chunk_id -> normalized score in [0, 1].
    """

    toks = _tokenize(query)
    if not toks:
        return {}

    limit = max(1, min(int(limit), 2000))
    q_vec = embedder.embed([query]).reshape(-1).astype(np.float32)
    q_lit = _vec_to_pgvector_literal(q_vec)
    tenant_id = current_tenant_id()

    with conn.cursor() as cur:
        cur.execute(
            """
            WITH q AS (SELECT %s::vector AS v)
            SELECT e.chunk_id, (1 - (e.vec <=> q.v)) AS score
            FROM embeddings e
            JOIN chunks c ON c.chunk_id = e.chunk_id,
                 q
            WHERE c.tenant_id = %s
            ORDER BY e.vec <=> q.v
            LIMIT %s
            """,
            (q_lit, tenant_id, limit),
        )
        rows = cur.fetchall()

    scores = {str(r["chunk_id"]): float(r["score"]) for r in rows if r.get("chunk_id") is not None}
    if not scores:
        return {}

    # Normalize to [0,1] by shifting min to 0 and scaling max to 1.
    vals = list(scores.values())
    mn = min(vals)
    shifted = {cid: (s - mn) for cid, s in scores.items()}
    mx2 = max(shifted.values())
    if mx2 > 0:
        shifted = {cid: (s / mx2) for cid, s in shifted.items()}
    return shifted


def _retrieve_postgres(
    conn: Any,
    question: str,
    *,
    top_k: int,
    lexical_limit: int,
    vector_limit: int,
    lexical_weight: float,
    vector_weight: float,
    embedder: Embedder,
    use_vector: bool,
) -> list[RetrievedChunk]:
    lexical_start = time.perf_counter()
    lex = _pg_lexical_scores(conn, question, lexical_limit)
    lexical_ms = (time.perf_counter() - lexical_start) * 1000.0

    vector_ms = 0.0
    if use_vector:
        vector_start = time.perf_counter()
        vec = _pg_vector_scores(conn, question, embedder, vector_limit)
        vector_ms = (time.perf_counter() - vector_start) * 1000.0
    else:
        vec = {}

    cand_ids = set(lex.keys()) | set(vec.keys())
    if not cand_ids:
        _log_retrieval_diagnostics(
            backend="postgres",
            top_k=top_k,
            lexical_limit=lexical_limit,
            vector_limit=vector_limit,
            lexical_weight=lexical_weight,
            vector_weight=vector_weight,
            lexical_candidates=0,
            vector_candidates=0,
            merged_candidates=0,
            lexical_ms=lexical_ms,
            vector_ms=vector_ms,
            merge_ms=0.0,
        )
        return []

    merge_start = time.perf_counter()
    # Fetch chunk records for candidates.
    chunk_ids = list(cand_ids)
    chunks = get_chunks_by_ids(conn, chunk_ids)
    now_i = int(time.time())
    expired_doc_ids = _expired_doc_ids_for_doc_ids(conn, {c.doc_id for c in chunks}, now=now_i)
    by_id = {c.chunk_id: c for c in chunks}

    scored: list[RetrievedChunk] = []
    for cid in cand_ids:
        c = by_id.get(cid)
        if c is None:
            continue
        if c.doc_id in expired_doc_ids:
            continue
        lex_s = float(lex.get(cid, 0.0))
        vec_s = float(vec.get(cid, 0.0))
        score = (lexical_weight * lex_s) + (vector_weight * vec_s)
        scored.append(
            RetrievedChunk(
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                idx=c.idx,
                text=c.text,
                score=score,
                lexical_score=lex_s,
                vector_score=vec_s,
            )
        )

    scored.sort(key=_retrieval_sort_key)
    merge_ms = (time.perf_counter() - merge_start) * 1000.0
    _log_retrieval_diagnostics(
        backend="postgres",
        top_k=top_k,
        lexical_limit=lexical_limit,
        vector_limit=vector_limit,
        lexical_weight=lexical_weight,
        vector_weight=vector_weight,
        lexical_candidates=len(lex),
        vector_candidates=len(vec),
        merged_candidates=len(scored),
        lexical_ms=lexical_ms,
        vector_ms=vector_ms,
        merge_ms=merge_ms,
    )
    return scored[: max(1, min(int(top_k), 50))]

def _lexical_scores_bm25(tokenized_chunks: list[list[str]], query: str) -> dict[int, float]:
    """Fallback lexical scorer: BM25 via rank_bm25 over all chunks.

    Returns dict chunk_index -> lexical_score in [0,1].
    """

    try:
        from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]
    except Exception:
        q = set(_tokenize(query))
        if not q:
            return {}
        scores: dict[int, float] = {}
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
    lexical_limit: int | None = None,
    vector_limit: int | None = None,
) -> list[RetrievedChunk]:
    """Hybrid retrieval:

    - lexical: FTS5 BM25 (preferred) or BM25Okapi fallback
    - vector: cosine similarity
    - combine: average of normalized lexical + vector
    """

    top_k = max(1, min(int(top_k or settings.top_k_default), 50))
    lexical_limit = max(1, min(int(lexical_limit or settings.retrieval_lexical_limit), 2000))
    vector_limit = max(1, min(int(vector_limit or settings.retrieval_vector_limit), 2000))
    use_vector = settings.embeddings_backend != "none"
    lexical_weight, vector_weight = effective_hybrid_weights(use_vector=use_vector)
    embedder = _get_embedder()

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        now_i = int(time.time())

        # Postgres path: use DB-native lexical + pgvector search (avoid loading entire corpus into memory).
        if settings.database_url:
            return _retrieve_postgres(
                conn,
                question,
                top_k=top_k,
                lexical_limit=lexical_limit,
                vector_limit=vector_limit,
                lexical_weight=lexical_weight,
                vector_weight=vector_weight,
                embedder=embedder,
                use_vector=use_vector,
            )

        # If settings changed (backend/model/dim), rebuild stored embeddings so retrieval stays valid.
        rebuilt = False
        if not settings.database_url:
            rebuilt = ensure_index_compatible(conn, embedder)
        conn.commit()
        if rebuilt:
            invalidate_cache()
        chunks, emb_mat, tokenized = _load_corpus(conn)

        if not chunks:
            return []

        expired_doc_ids = _expired_doc_ids_for_doc_ids(conn, {c.doc_id for c in chunks}, now=now_i)
        if len(expired_doc_ids) == len({c.doc_id for c in chunks}):
            return []
        active_chunk_indexes = [i for i, c in enumerate(chunks) if c.doc_id not in expired_doc_ids]
        active_chunk_index_set = set(active_chunk_indexes)
        if not active_chunk_indexes:
            return []

        # Lexical
        lexical_start = time.perf_counter()
        lex_fts = _lexical_scores_fts(conn, question, lexical_limit)
        if lex_fts is not None:
            index_of = {c.chunk_id: i for i, c in enumerate(chunks)}
            lex_scores = {
                index_of[cid]: s
                for cid, s in lex_fts.items()
                if cid in index_of and index_of[cid] in active_chunk_index_set
            }
        else:
            lex_scores = {
                i: s for i, s in _lexical_scores_bm25(tokenized, question).items() if i in active_chunk_index_set
            }
        lexical_ms = (time.perf_counter() - lexical_start) * 1000.0

        # Vector (optional)
        vector_ms = 0.0
        if use_vector:
            vector_start = time.perf_counter()
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
            vector_ms = (time.perf_counter() - vector_start) * 1000.0
        else:
            sims = np.zeros((len(chunks),), dtype=np.float32)

        merge_start = time.perf_counter()
        cand_idx: set[int] = set()
        top_vec_idx: list[int] = []
        if lex_scores:
            top_lex = sorted(lex_scores.items(), key=lambda kv: kv[1], reverse=True)[:lexical_limit]
            cand_idx.update(i for i, _ in top_lex)

        if use_vector:
            top_vec_idx = np.argsort(-sims)[:vector_limit].tolist()
            cand_idx.update(int(i) for i in top_vec_idx if int(i) in active_chunk_index_set)

        results: list[RetrievedChunk] = []
        for i in cand_idx:
            c = chunks[i]
            if c.doc_id in expired_doc_ids:
                continue
            lex_score = float(lex_scores.get(i, 0.0))
            vec_score = float(sims[i])
            score = (lexical_weight * lex_score) + (vector_weight * vec_score)
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

        results.sort(key=_retrieval_sort_key)
        merge_ms = (time.perf_counter() - merge_start) * 1000.0
        _log_retrieval_diagnostics(
            backend="sqlite",
            top_k=top_k,
            lexical_limit=lexical_limit,
            vector_limit=vector_limit,
            lexical_weight=lexical_weight,
            vector_weight=vector_weight,
            lexical_candidates=len(lex_scores),
            vector_candidates=len(top_vec_idx),
            merged_candidates=len(results),
            lexical_ms=lexical_ms,
            vector_ms=vector_ms,
            merge_ms=merge_ms,
        )
        return results[:top_k]
