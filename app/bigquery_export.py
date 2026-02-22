from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


JSONDict = dict[str, object]
RowMapper = Callable[[dict[str, Any]], JSONDict]


@dataclass(frozen=True)
class ExportField:
    name: str
    field_type: str
    mode: str = "NULLABLE"
    description: str = ""


@dataclass(frozen=True)
class ExportTableSpec:
    name: str
    select_sql: str
    schema: tuple[ExportField, ...]
    map_row: RowMapper


@dataclass(frozen=True)
class BigQueryLoadResult:
    table_id: str
    rows_exported: int
    load_job_ids: tuple[str, ...]


def _is_postgres_conn(conn: Any) -> bool:
    return "psycopg" in type(conn).__module__


def _parse_json_list(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(v) for v in raw if str(v).strip()]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except Exception:
            return []
        if isinstance(parsed, list):
            return [str(v) for v in parsed if str(v).strip()]
    return []


def _map_doc_row(row: dict[str, Any]) -> JSONDict:
    return {
        "doc_id": str(row["doc_id"]),
        "title": str(row["title"]),
        "source": str(row["source"]),
        "classification": str(row["classification"]),
        "retention": str(row["retention"]),
        "tags": _parse_json_list(row.get("tags_json")),
        "content_sha256": row.get("content_sha256"),
        "content_bytes": int(row["content_bytes"]),
        "num_chunks": int(row["num_chunks"]),
        "doc_version": int(row["doc_version"]),
        "created_at": int(row["created_at"]),
        "updated_at": int(row["updated_at"]),
    }


def _map_ingest_event_row(row: dict[str, Any]) -> JSONDict:
    return {
        "event_id": str(row["event_id"]),
        "doc_id": str(row["doc_id"]),
        "doc_version": int(row["doc_version"]),
        "ingested_at": int(row["ingested_at"]),
        "content_sha256": str(row["content_sha256"]),
        "prev_content_sha256": row.get("prev_content_sha256"),
        "changed": bool(int(row["changed"])),
        "num_chunks": int(row["num_chunks"]),
        "embedding_backend": str(row["embedding_backend"]),
        "embeddings_model": str(row["embeddings_model"]),
        "embedding_dim": int(row["embedding_dim"]),
        "chunk_size_chars": int(row["chunk_size_chars"]),
        "chunk_overlap_chars": int(row["chunk_overlap_chars"]),
        "classification": str(row["classification"]),
        "retention": str(row["retention"]),
        "tags": _parse_json_list(row.get("tags_json")),
        "schema_fingerprint": row.get("schema_fingerprint"),
        "contract_sha256": row.get("contract_sha256"),
        "validation_status": row.get("validation_status"),
        "validation_errors": _parse_json_list(row.get("validation_errors_json")),
        "schema_drifted": bool(int(row.get("schema_drifted") or 0)),
        "run_id": row.get("run_id"),
        "notes": row.get("notes"),
    }


def _map_eval_run_row(row: dict[str, Any]) -> JSONDict:
    return {
        "run_id": str(row["run_id"]),
        "started_at": int(row["started_at"]),
        "finished_at": int(row["finished_at"]) if row.get("finished_at") is not None else None,
        "status": str(row["status"]),
        "dataset_name": str(row["dataset_name"]),
        "dataset_sha256": str(row["dataset_sha256"]),
        "k": int(row["k"]),
        "include_details": bool(int(row["include_details"])),
        "app_version": str(row["app_version"]),
        "embeddings_backend": str(row["embeddings_backend"]),
        "embeddings_model": str(row["embeddings_model"]),
        "retrieval_config_json": str(row["retrieval_config_json"]),
        "provider_config_json": str(row["provider_config_json"]),
        "summary_json": str(row["summary_json"]),
        "diff_from_prev_json": str(row["diff_from_prev_json"]),
        "details_json": str(row["details_json"]),
        "error": row.get("error"),
    }


EXPORT_TABLES: tuple[ExportTableSpec, ...] = (
    ExportTableSpec(
        name="docs",
        select_sql="""
            SELECT
              doc_id,
              title,
              source,
              classification,
              retention,
              tags_json,
              content_sha256,
              content_bytes,
              num_chunks,
              doc_version,
              created_at,
              updated_at
            FROM docs
            ORDER BY doc_id ASC
        """,
        schema=(
            ExportField("doc_id", "STRING", "REQUIRED"),
            ExportField("title", "STRING", "REQUIRED"),
            ExportField("source", "STRING", "REQUIRED"),
            ExportField("classification", "STRING", "REQUIRED"),
            ExportField("retention", "STRING", "REQUIRED"),
            ExportField("tags", "STRING", "REPEATED"),
            ExportField("content_sha256", "STRING"),
            ExportField("content_bytes", "INT64", "REQUIRED"),
            ExportField("num_chunks", "INT64", "REQUIRED"),
            ExportField("doc_version", "INT64", "REQUIRED"),
            ExportField("created_at", "INT64", "REQUIRED"),
            ExportField("updated_at", "INT64", "REQUIRED"),
        ),
        map_row=_map_doc_row,
    ),
    ExportTableSpec(
        name="ingest_events",
        select_sql="""
            SELECT
              e.event_id,
              e.doc_id,
              e.doc_version,
              e.ingested_at,
              e.content_sha256,
              e.prev_content_sha256,
              e.changed,
              e.num_chunks,
              e.embedding_backend,
              e.embeddings_model,
              e.embedding_dim,
              e.chunk_size_chars,
              e.chunk_overlap_chars,
              e.schema_fingerprint,
              e.contract_sha256,
              e.validation_status,
              e.validation_errors_json,
              e.schema_drifted,
              e.run_id,
              e.notes,
              d.classification,
              d.retention,
              d.tags_json
            FROM ingest_events e
            JOIN docs d ON d.doc_id = e.doc_id
            ORDER BY e.event_id ASC
        """,
        schema=(
            ExportField("event_id", "STRING", "REQUIRED"),
            ExportField("doc_id", "STRING", "REQUIRED"),
            ExportField("doc_version", "INT64", "REQUIRED"),
            ExportField("ingested_at", "INT64", "REQUIRED"),
            ExportField("content_sha256", "STRING", "REQUIRED"),
            ExportField("prev_content_sha256", "STRING"),
            ExportField("changed", "BOOL", "REQUIRED"),
            ExportField("num_chunks", "INT64", "REQUIRED"),
            ExportField("embedding_backend", "STRING", "REQUIRED"),
            ExportField("embeddings_model", "STRING", "REQUIRED"),
            ExportField("embedding_dim", "INT64", "REQUIRED"),
            ExportField("chunk_size_chars", "INT64", "REQUIRED"),
            ExportField("chunk_overlap_chars", "INT64", "REQUIRED"),
            ExportField("classification", "STRING", "REQUIRED"),
            ExportField("retention", "STRING", "REQUIRED"),
            ExportField("tags", "STRING", "REPEATED"),
            ExportField("schema_fingerprint", "STRING"),
            ExportField("contract_sha256", "STRING"),
            ExportField("validation_status", "STRING"),
            ExportField("validation_errors", "STRING", "REPEATED"),
            ExportField("schema_drifted", "BOOL", "REQUIRED"),
            ExportField("run_id", "STRING"),
            ExportField("notes", "STRING"),
        ),
        map_row=_map_ingest_event_row,
    ),
    ExportTableSpec(
        name="eval_runs",
        select_sql="""
            SELECT
              run_id,
              started_at,
              finished_at,
              status,
              dataset_name,
              dataset_sha256,
              k,
              include_details,
              app_version,
              embeddings_backend,
              embeddings_model,
              retrieval_config_json,
              provider_config_json,
              summary_json,
              diff_from_prev_json,
              details_json,
              error
            FROM eval_runs
            ORDER BY run_id ASC
        """,
        schema=(
            ExportField("run_id", "STRING", "REQUIRED"),
            ExportField("started_at", "INT64", "REQUIRED"),
            ExportField("finished_at", "INT64"),
            ExportField("status", "STRING", "REQUIRED"),
            ExportField("dataset_name", "STRING", "REQUIRED"),
            ExportField("dataset_sha256", "STRING", "REQUIRED"),
            ExportField("k", "INT64", "REQUIRED"),
            ExportField("include_details", "BOOL", "REQUIRED"),
            ExportField("app_version", "STRING", "REQUIRED"),
            ExportField("embeddings_backend", "STRING", "REQUIRED"),
            ExportField("embeddings_model", "STRING", "REQUIRED"),
            ExportField("retrieval_config_json", "STRING", "REQUIRED"),
            ExportField("provider_config_json", "STRING", "REQUIRED"),
            ExportField("summary_json", "STRING", "REQUIRED"),
            ExportField("diff_from_prev_json", "STRING", "REQUIRED"),
            ExportField("details_json", "STRING", "REQUIRED"),
            ExportField("error", "STRING"),
        ),
        map_row=_map_eval_run_row,
    ),
)


def get_export_table(name: str) -> ExportTableSpec:
    for spec in EXPORT_TABLES:
        if spec.name == name:
            return spec
    raise KeyError(f"unknown export table: {name}")


def chunk_rows(rows: Iterable[JSONDict], *, chunk_size: int) -> Iterator[list[JSONDict]]:
    chunk_size_i = max(1, int(chunk_size))
    chunk: list[JSONDict] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) >= chunk_size_i:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _fetch_rows(conn: Any, spec: ExportTableSpec, *, limit: int, offset: int) -> list[dict[str, Any]]:
    if _is_postgres_conn(conn):
        cur = conn.execute(f"{spec.select_sql}\nLIMIT %s OFFSET %s", (int(limit), int(offset)))
    else:
        cur = conn.execute(f"{spec.select_sql}\nLIMIT ? OFFSET ?", (int(limit), int(offset)))
    return [dict(r) for r in cur.fetchall()]


def iter_table_rows(
    conn: Any,
    spec: ExportTableSpec,
    *,
    batch_size: int = 500,
) -> Iterator[JSONDict]:
    batch = max(1, min(int(batch_size), 10_000))
    offset = 0
    while True:
        rows = _fetch_rows(conn, spec, limit=batch, offset=offset)
        if not rows:
            return
        for row in rows:
            yield spec.map_row(row)
        offset += len(rows)


def export_jsonl_snapshot(
    conn: Any,
    *,
    output_dir: str | Path,
    batch_size: int = 500,
) -> dict[str, int]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    for spec in EXPORT_TABLES:
        tmp_path = out_dir / f".{spec.name}.jsonl.tmp"
        target_path = out_dir / f"{spec.name}.jsonl"
        written = 0
        with tmp_path.open("w", encoding="utf-8") as handle:
            rows = iter_table_rows(conn, spec, batch_size=batch_size)
            for chunk in chunk_rows(rows, chunk_size=batch_size):
                for row in chunk:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                    handle.write("\n")
                    written += 1
        tmp_path.replace(target_path)
        counts[spec.name] = written

    manifest_path = out_dir / "manifest.json"
    manifest = {
        "exported_at": int(time.time()),
        "tables": counts,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return counts


def _validate_dataset_name(dataset: str) -> str:
    clean = dataset.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clean):
        raise ValueError("dataset must match [A-Za-z_][A-Za-z0-9_]*")
    return clean


def _validate_table_prefix(prefix: str) -> str:
    clean = prefix.strip()
    if not clean:
        raise ValueError("table_prefix cannot be empty")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clean):
        raise ValueError("table_prefix must match [A-Za-z_][A-Za-z0-9_]*")
    return clean


def _bigquery_client(project_id: str) -> Any:
    bigquery = _bigquery_module()
    return bigquery.Client(project=project_id)


def _bigquery_module() -> Any:
    try:
        return import_module("google.cloud.bigquery")
    except Exception as e:  # pragma: no cover - dependency is optional
        raise RuntimeError(
            "google-cloud-bigquery is not installed. Install with `uv pip install google-cloud-bigquery`."
        ) from e


def export_to_bigquery(
    conn: Any,
    *,
    project_id: str,
    dataset: str,
    table_prefix: str = "gkp_",
    batch_size: int = 500,
    location: str | None = None,
) -> dict[str, BigQueryLoadResult]:
    project = project_id.strip()
    if not project:
        raise ValueError("project_id is required")

    dataset_clean = _validate_dataset_name(dataset)
    table_prefix_clean = _validate_table_prefix(table_prefix)

    bigquery = _bigquery_module()
    client = _bigquery_client(project)
    dataset_ref = bigquery.Dataset(f"{project}.{dataset_clean}")
    client.create_dataset(dataset_ref, exists_ok=True)

    results: dict[str, BigQueryLoadResult] = {}

    for spec in EXPORT_TABLES:
        table_id = f"{project}.{dataset_clean}.{table_prefix_clean}{spec.name}"
        schema = [bigquery.SchemaField(f.name, f.field_type, mode=f.mode, description=f.description) for f in spec.schema]
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table, exists_ok=True)

        first_chunk = True
        rows_exported = 0
        job_ids: list[str] = []

        rows = iter_table_rows(conn, spec, batch_size=batch_size)
        for chunk in chunk_rows(rows, chunk_size=batch_size):
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=(
                    bigquery.WriteDisposition.WRITE_TRUNCATE
                    if first_chunk
                    else bigquery.WriteDisposition.WRITE_APPEND
                ),
            )
            if location:
                load_job = client.load_table_from_json(chunk, table_id, job_config=job_config, location=location)
            else:
                load_job = client.load_table_from_json(chunk, table_id, job_config=job_config)
            load_job.result()
            if load_job.job_id:
                job_ids.append(str(load_job.job_id))
            rows_exported += len(chunk)
            first_chunk = False

        # Ensure an idempotent rerun clears stale rows even when the source table is empty.
        if first_chunk:
            truncate_sql = f"TRUNCATE TABLE `{table_id}`"
            if location:
                truncate_job = client.query(truncate_sql, location=location)
            else:
                truncate_job = client.query(truncate_sql)
            truncate_job.result()
            if truncate_job.job_id:
                job_ids.append(str(truncate_job.job_id))

        results[spec.name] = BigQueryLoadResult(
            table_id=table_id,
            rows_exported=rows_exported,
            load_job_ids=tuple(job_ids),
        )

    return results
