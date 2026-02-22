from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .config import settings
from .embeddings import Embedder, HashEmbedder, NoEmbedder, SentenceTransformerEmbedder
from .storage import connect, init_db
from .tenant import normalize_tenant_id, reset_tenant_id, set_tenant_id

LEXICAL_INDEX_NAME = "idx_chunks_fts"
VECTOR_INDEX_NAME = "idx_embeddings_vec_hnsw"


@dataclass(frozen=True)
class PlanSummary:
    expected_index: str
    index_used: bool
    indexes_seen: tuple[str, ...]
    seq_scan_relations: tuple[str, ...]
    planning_time_ms: float
    execution_time_ms: float
    plan_rows: int | None
    total_cost: float | None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "expected_index": self.expected_index,
            "index_used": bool(self.index_used),
            "indexes_seen": list(self.indexes_seen),
            "seq_scan_relations": list(self.seq_scan_relations),
            "planning_time_ms": float(self.planning_time_ms),
            "execution_time_ms": float(self.execution_time_ms),
            "plan_rows": self.plan_rows,
            "total_cost": self.total_cost,
            "error": self.error,
        }


@dataclass(frozen=True)
class QueryProfile:
    question: str
    lexical: PlanSummary
    vector: PlanSummary | None = None
    lexical_plan_json: dict[str, object] | None = None
    vector_plan_json: dict[str, object] | None = None

    def to_dict(self, *, include_plans: bool) -> dict[str, object]:
        out: dict[str, object] = {
            "question": self.question,
            "lexical": self.lexical.to_dict(),
            "vector": self.vector.to_dict() if self.vector is not None else None,
        }
        if include_plans:
            out["lexical_plan_json"] = self.lexical_plan_json
            out["vector_plan_json"] = self.vector_plan_json
        return out


@dataclass(frozen=True)
class RetrievalProfileReport:
    generated_at: int
    tenant_id: str
    database_backend: str
    query_count: int
    lexical_index_name: str
    vector_index_name: str
    lexical_index_hits: int
    vector_index_hits: int
    profiles: tuple[QueryProfile, ...]

    def to_dict(self, *, include_plans: bool) -> dict[str, object]:
        return {
            "generated_at": int(self.generated_at),
            "tenant_id": self.tenant_id,
            "database_backend": self.database_backend,
            "query_count": int(self.query_count),
            "lexical_index_name": self.lexical_index_name,
            "vector_index_name": self.vector_index_name,
            "lexical_index_hits": int(self.lexical_index_hits),
            "vector_index_hits": int(self.vector_index_hits),
            "profiles": [p.to_dict(include_plans=include_plans) for p in self.profiles],
        }


def _is_postgres_conn(conn: Any) -> bool:
    return "psycopg" in type(conn).__module__


def _iter_plan_nodes(node: dict[str, Any]):
    yield node
    for child in node.get("Plans") or []:
        if isinstance(child, dict):
            yield from _iter_plan_nodes(child)


def summarize_plan_json(
    plan_json: dict[str, Any],
    *,
    expected_index: str,
) -> PlanSummary:
    root = plan_json.get("Plan")
    if not isinstance(root, dict):
        return PlanSummary(
            expected_index=expected_index,
            index_used=False,
            indexes_seen=tuple(),
            seq_scan_relations=tuple(),
            planning_time_ms=0.0,
            execution_time_ms=0.0,
            plan_rows=None,
            total_cost=None,
            error="Plan JSON missing top-level Plan object",
        )

    indexes: set[str] = set()
    seq_scans: set[str] = set()
    for node in _iter_plan_nodes(root):
        idx = node.get("Index Name")
        if isinstance(idx, str) and idx.strip():
            indexes.add(idx.strip())

        node_type = str(node.get("Node Type") or "")
        relation = str(node.get("Relation Name") or "").strip()
        if "Seq Scan" in node_type and relation:
            seq_scans.add(relation)

    planning_ms = float(plan_json.get("Planning Time") or 0.0)
    execution_ms = float(plan_json.get("Execution Time") or 0.0)

    plan_rows: int | None
    raw_rows = root.get("Plan Rows")
    if isinstance(raw_rows, (int, float)):
        plan_rows = int(raw_rows)
    else:
        plan_rows = None

    total_cost: float | None
    raw_cost = root.get("Total Cost")
    if isinstance(raw_cost, (int, float)):
        total_cost = float(raw_cost)
    else:
        total_cost = None

    sorted_indexes = tuple(sorted(indexes))
    return PlanSummary(
        expected_index=expected_index,
        index_used=expected_index in indexes,
        indexes_seen=sorted_indexes,
        seq_scan_relations=tuple(sorted(seq_scans)),
        planning_time_ms=planning_ms,
        execution_time_ms=execution_ms,
        plan_rows=plan_rows,
        total_cost=total_cost,
        error=None,
    )


def _embedder() -> Embedder:
    backend = settings.embeddings_backend
    if backend == "none":
        return NoEmbedder()
    if backend == "hash":
        return HashEmbedder(dim=settings.embedding_dim)
    if backend == "sentence-transformers":
        return SentenceTransformerEmbedder(settings.embeddings_model)
    return HashEmbedder(dim=settings.embedding_dim)


def _default_queries_from_dataset(path: Path, *, limit: int) -> list[str]:
    if not path.exists():
        return []

    out: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        question = str(obj.get("question") or "").strip()
        if not question:
            continue
        out.append(question)
        if len(out) >= limit:
            break
    return out


def default_profile_queries(*, limit: int = 5) -> list[str]:
    dataset_queries = _default_queries_from_dataset(Path("data/eval/smoke.jsonl"), limit=limit)
    if dataset_queries:
        return dataset_queries

    return [
        "Why use Cloud SQL for persistence?",
        "What is a BigQuery lakehouse pattern?",
        "How do streaming pipelines use Pub/Sub and Dataflow?",
    ][: max(1, int(limit))]


def _normalize_query_vector(question: str, *, dim: int) -> np.ndarray:
    vec = _embedder().embed([question]).reshape(-1).astype(np.float32)
    if vec.size != int(dim):
        adjusted = np.zeros((int(dim),), dtype=np.float32)
        n = min(int(dim), int(vec.size))
        adjusted[:n] = vec[:n]
        vec = adjusted
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm
    return vec


def _vec_to_pgvector_literal(vec: np.ndarray) -> str:
    vals = vec.reshape(-1).astype(np.float32).tolist()
    return "[" + ",".join(str(float(v)) for v in vals) + "]"


def _explain_json(conn: Any, sql: str, params: tuple[object, ...]) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}", params)
        row = cur.fetchone()

    if row is None:
        raise RuntimeError("EXPLAIN did not return a plan")

    payload = row[0]
    if isinstance(payload, str):
        decoded = json.loads(payload)
    else:
        decoded = payload

    if isinstance(decoded, list) and decoded and isinstance(decoded[0], dict):
        return decoded[0]
    if isinstance(decoded, dict):
        return decoded
    raise RuntimeError("Unexpected EXPLAIN JSON payload shape")


def _plan_error(expected_index: str, message: str) -> PlanSummary:
    return PlanSummary(
        expected_index=expected_index,
        index_used=False,
        indexes_seen=tuple(),
        seq_scan_relations=tuple(),
        planning_time_ms=0.0,
        execution_time_ms=0.0,
        plan_rows=None,
        total_cost=None,
        error=message,
    )


def profile_retrieval_queries(
    *,
    queries: list[str],
    tenant_id: str,
    top_k: int,
) -> RetrievalProfileReport:
    tenant = normalize_tenant_id(tenant_id)
    if not queries:
        raise ValueError("At least one query is required")

    token = set_tenant_id(tenant)
    try:
        with connect(settings.sqlite_path) as conn:
            init_db(conn)
            if not _is_postgres_conn(conn):
                raise RuntimeError("Retrieval profiling requires Postgres (set DATABASE_URL)")

            dim: int | None = None
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.dim
                    FROM embeddings e
                    JOIN chunks c ON c.chunk_id = e.chunk_id
                    WHERE c.tenant_id = %s
                    LIMIT 1
                    """,
                    (tenant,),
                )
                row = cur.fetchone()
                if row is not None:
                    dim = int(row["dim"])

            profiles: list[QueryProfile] = []
            lexical_hits = 0
            vector_hits = 0
            for question in queries:
                lexical_sql = """
                WITH q AS (SELECT plainto_tsquery('english', %s) AS query)
                SELECT c.chunk_id, ts_rank_cd(to_tsvector('english', c.text), q.query) AS score
                FROM chunks c, q
                WHERE to_tsvector('english', c.text) @@ q.query
                  AND c.tenant_id = %s
                ORDER BY score DESC
                LIMIT %s
                """

                try:
                    lexical_plan = _explain_json(conn, lexical_sql, (question, tenant, int(top_k)))
                    lexical_summary = summarize_plan_json(lexical_plan, expected_index=LEXICAL_INDEX_NAME)
                except Exception as e:  # pragma: no cover - exercised in integration use
                    lexical_plan = None
                    lexical_summary = _plan_error(LEXICAL_INDEX_NAME, str(e))

                if lexical_summary.index_used:
                    lexical_hits += 1

                vector_plan: dict[str, Any] | None = None
                if dim is None:
                    vector_summary = _plan_error(VECTOR_INDEX_NAME, "No embeddings found for tenant")
                else:
                    try:
                        q_vec = _normalize_query_vector(question, dim=dim)
                        q_lit = _vec_to_pgvector_literal(q_vec)
                        vector_sql = """
                        WITH q AS (SELECT %s::vector AS v)
                        SELECT e.chunk_id, (1 - (e.vec <=> q.v)) AS score
                        FROM embeddings e
                        JOIN chunks c ON c.chunk_id = e.chunk_id, q
                        WHERE c.tenant_id = %s
                        ORDER BY e.vec <=> q.v
                        LIMIT %s
                        """
                        vector_plan = _explain_json(conn, vector_sql, (q_lit, tenant, int(top_k)))
                        vector_summary = summarize_plan_json(vector_plan, expected_index=VECTOR_INDEX_NAME)
                    except Exception as e:  # pragma: no cover - exercised in integration use
                        vector_summary = _plan_error(VECTOR_INDEX_NAME, str(e))

                if vector_summary.index_used:
                    vector_hits += 1

                profiles.append(
                    QueryProfile(
                        question=question,
                        lexical=lexical_summary,
                        vector=vector_summary,
                        lexical_plan_json=lexical_plan,
                        vector_plan_json=vector_plan,
                    )
                )

            return RetrievalProfileReport(
                generated_at=int(time.time()),
                tenant_id=tenant,
                database_backend="postgres",
                query_count=len(queries),
                lexical_index_name=LEXICAL_INDEX_NAME,
                vector_index_name=VECTOR_INDEX_NAME,
                lexical_index_hits=lexical_hits,
                vector_index_hits=vector_hits,
                profiles=tuple(profiles),
            )
    finally:
        reset_tenant_id(token)


def print_retrieval_profile(report: RetrievalProfileReport) -> None:
    total = max(1, int(report.query_count))
    print("Retrieval profiling summary")
    print(f"tenant_id={report.tenant_id} backend={report.database_backend} queries={report.query_count}")
    print(
        "lexical index usage "
        f"({report.lexical_index_name}): {report.lexical_index_hits}/{total} "
        f"({(100.0 * report.lexical_index_hits / total):.1f}%)"
    )
    print(
        "vector index usage "
        f"({report.vector_index_name}): {report.vector_index_hits}/{total} "
        f"({(100.0 * report.vector_index_hits / total):.1f}%)"
    )
    print("")

    for idx, qp in enumerate(report.profiles, start=1):
        print(f"[{idx}] query={qp.question!r}")

        lex = qp.lexical
        lex_seq = ",".join(lex.seq_scan_relations) if lex.seq_scan_relations else "none"
        print(
            "  lexical: "
            f"index_used={'yes' if lex.index_used else 'no'} "
            f"planning_ms={lex.planning_time_ms:.2f} exec_ms={lex.execution_time_ms:.2f} "
            f"seq_scans={lex_seq}"
            + (f" error={lex.error}" if lex.error else "")
        )

        vec = qp.vector
        if vec is None:
            print("  vector: skipped")
            continue
        vec_seq = ",".join(vec.seq_scan_relations) if vec.seq_scan_relations else "none"
        print(
            "  vector: "
            f"index_used={'yes' if vec.index_used else 'no'} "
            f"planning_ms={vec.planning_time_ms:.2f} exec_ms={vec.execution_time_ms:.2f} "
            f"seq_scans={vec_seq}"
            + (f" error={vec.error}" if vec.error else "")
        )


def cmd_profile_retrieval(
    *,
    queries: list[str],
    tenant_id: str,
    top_k: int,
    json_out: str | None,
    include_plans: bool,
) -> None:
    selected_queries = [q.strip() for q in queries if q.strip()]
    if not selected_queries:
        selected_queries = default_profile_queries(limit=5)

    try:
        report = profile_retrieval_queries(
            queries=selected_queries,
            tenant_id=tenant_id,
            top_k=max(1, min(int(top_k), 2000)),
        )
    except RuntimeError as e:
        raise SystemExit(str(e)) from e
    print_retrieval_profile(report)

    if json_out:
        out_path = Path(json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(report.to_dict(include_plans=include_plans), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote report JSON: {out_path}")
