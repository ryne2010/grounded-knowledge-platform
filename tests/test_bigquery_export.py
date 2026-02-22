from __future__ import annotations

import json
from pathlib import Path

from app.bigquery_export import chunk_rows, export_jsonl_snapshot, get_export_table, iter_table_rows
from app.storage import IngestEvent, connect, init_db, insert_eval_run, insert_ingest_event, upsert_doc


def _seed_export_source_data(sqlite_path: Path) -> None:
    with connect(str(sqlite_path)) as conn:
        init_db(conn)
        upsert_doc(
            conn,
            doc_id="doc-1",
            title="Cloud SQL Guide",
            source="gs://bucket/cloudsql.md",
            classification="internal",
            retention="90d",
            tags_json='["ops","governance"]',
            content_sha256="sha-doc-v2",
            content_bytes=1234,
            num_chunks=4,
            doc_version=2,
        )
        insert_ingest_event(
            conn,
            IngestEvent(
                event_id="evt-1",
                doc_id="doc-1",
                doc_version=2,
                ingested_at=1_706_000_000,
                content_sha256="sha-doc-v2",
                prev_content_sha256="sha-doc-v1",
                changed=1,
                num_chunks=4,
                embedding_backend="hash",
                embeddings_model="hash-v1",
                embedding_dim=512,
                chunk_size_chars=1200,
                chunk_overlap_chars=200,
                schema_fingerprint="schema:abc",
                contract_sha256="contract:def",
                validation_status="warn",
                validation_errors_json='["missing:owner"]',
                schema_drifted=1,
                run_id="run-123",
                notes="source refresh",
            ),
        )
        insert_eval_run(
            conn,
            run_id="eval-1",
            started_at=1_706_000_100,
            finished_at=1_706_000_105,
            status="succeeded",
            dataset_name="data/eval/smoke.jsonl",
            dataset_sha256="dataset:123",
            k=5,
            include_details=False,
            app_version="0.10.0",
            embeddings_backend="hash",
            embeddings_model="hash-v1",
            retrieval_config_json='{"k":5}',
            provider_config_json='{"provider":"extractive"}',
            summary_json='{"examples":1,"passed":1,"failed":0}',
            diff_from_prev_json='{"previous_run_id":null}',
            details_json="[]",
            error=None,
        )
        conn.commit()


def test_export_mapping_includes_lineage_and_governance_fields(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "bigquery_export.sqlite"
    _seed_export_source_data(sqlite_path)

    with connect(str(sqlite_path)) as conn:
        init_db(conn)

        docs_rows = list(iter_table_rows(conn, get_export_table("docs"), batch_size=2))
        assert len(docs_rows) == 1
        docs_row = docs_rows[0]
        assert docs_row["doc_id"] == "doc-1"
        assert docs_row["doc_version"] == 2
        assert docs_row["content_sha256"] == "sha-doc-v2"
        assert docs_row["classification"] == "internal"
        assert docs_row["retention"] == "90d"
        assert docs_row["tags"] == ["ops", "governance"]

        ingest_rows = list(iter_table_rows(conn, get_export_table("ingest_events"), batch_size=2))
        assert len(ingest_rows) == 1
        ingest_row = ingest_rows[0]
        assert ingest_row["event_id"] == "evt-1"
        assert ingest_row["doc_id"] == "doc-1"
        assert ingest_row["doc_version"] == 2
        assert ingest_row["content_sha256"] == "sha-doc-v2"
        assert ingest_row["classification"] == "internal"
        assert ingest_row["retention"] == "90d"
        assert ingest_row["validation_errors"] == ["missing:owner"]
        assert ingest_row["schema_drifted"] is True

        eval_rows = list(iter_table_rows(conn, get_export_table("eval_runs"), batch_size=2))
        assert len(eval_rows) == 1
        eval_row = eval_rows[0]
        assert eval_row["run_id"] == "eval-1"
        assert eval_row["dataset_name"] == "data/eval/smoke.jsonl"
        assert eval_row["summary_json"] == '{"examples":1,"passed":1,"failed":0}'


def test_chunk_rows_splits_without_data_loss() -> None:
    rows = [{"n": i} for i in range(7)]
    chunks = list(chunk_rows(rows, chunk_size=3))
    assert [len(chunk) for chunk in chunks] == [3, 3, 1]
    assert [int(row["n"]) for chunk in chunks for row in chunk] == list(range(7))


def test_jsonl_snapshot_export_is_idempotent(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "bigquery_export.sqlite"
    _seed_export_source_data(sqlite_path)
    out_dir = tmp_path / "export"

    with connect(str(sqlite_path)) as conn:
        init_db(conn)
        first_counts = export_jsonl_snapshot(conn, output_dir=out_dir, batch_size=2)
        first_docs = (out_dir / "docs.jsonl").read_text(encoding="utf-8")
        first_events = (out_dir / "ingest_events.jsonl").read_text(encoding="utf-8")
        first_eval = (out_dir / "eval_runs.jsonl").read_text(encoding="utf-8")

        second_counts = export_jsonl_snapshot(conn, output_dir=out_dir, batch_size=2)
        second_docs = (out_dir / "docs.jsonl").read_text(encoding="utf-8")
        second_events = (out_dir / "ingest_events.jsonl").read_text(encoding="utf-8")
        second_eval = (out_dir / "eval_runs.jsonl").read_text(encoding="utf-8")

    assert first_counts == {"docs": 1, "ingest_events": 1, "eval_runs": 1}
    assert second_counts == first_counts
    assert second_docs == first_docs
    assert second_events == first_events
    assert second_eval == first_eval

    docs_row = json.loads(first_docs.strip())
    events_row = json.loads(first_events.strip())
    assert docs_row["doc_id"] == events_row["doc_id"] == "doc-1"
