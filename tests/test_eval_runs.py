from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


_ENV_KEYS = [
    "SQLITE_PATH",
    "PUBLIC_DEMO_MODE",
    "AUTH_MODE",
    "API_KEYS_JSON",
    "ALLOW_CONNECTORS",
    "ALLOW_UPLOADS",
    "ALLOW_DOC_DELETE",
    "ALLOW_CHUNK_VIEW",
    "ALLOW_EVAL",
    "BOOTSTRAP_DEMO_CORPUS",
]


@pytest.fixture(autouse=True)
def _restore_env_after_test():
    before = {k: os.environ.get(k) for k in _ENV_KEYS}
    yield
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
            continue
        os.environ[key] = value


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = '{"reader-key":"reader","admin-key":"admin"}'
    os.environ["ALLOW_CONNECTORS"] = "1"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["ALLOW_DOC_DELETE"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["ALLOW_EVAL"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"

    import app.auth as auth
    import app.config as config
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(auth)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def _write_dataset(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    path.write_text(body + "\n", encoding="utf-8")


def test_eval_run_is_persisted_and_exposed_in_history_and_detail(tmp_path: Path) -> None:
    main = _reload_app(str(tmp_path / "eval_runs.sqlite"))
    client = TestClient(main.app)

    ingest = client.post(
        "/api/ingest/text",
        headers={"X-API-Key": "admin-key"},
        json={
            "title": "Eval Doc",
            "source": "unit-test",
            "text": "Cloud Run scales to zero and uses managed containers.",
        },
    )
    assert ingest.status_code == 200, ingest.text
    doc_id = str(ingest.json()["doc_id"])

    dataset_path = tmp_path / "datasets" / "golden_eval.jsonl"
    _write_dataset(
        dataset_path,
        [
            {
                "id": "eval-001",
                "question": "What can Cloud Run do?",
                "expected_doc_ids": [doc_id],
            }
        ],
    )

    run = client.post(
        "/api/eval/run",
        headers={"X-API-Key": "admin-key"},
        json={"golden_path": str(dataset_path), "k": 3, "include_details": True},
    )
    assert run.status_code == 200, run.text
    run_body = run.json()

    assert run_body["run_id"]
    assert run_body["examples"] == 1
    assert run_body["passed"] + run_body["failed"] == run_body["examples"]
    assert "app_version" in run_body
    assert "embeddings_backend" in run_body
    assert "embeddings_model" in run_body
    assert run_body["retrieval_config"]["k"] == 3
    assert "hybrid_weights" in run_body["retrieval_config"]
    assert "provider" in run_body["provider_config"]
    assert isinstance(run_body.get("details"), list)
    assert run_body["details"][0]["case_id"] == "eval-001"
    assert run_body["details"][0]["status"] in {"pass", "fail"}

    forbidden = client.get("/api/eval/runs", headers={"X-API-Key": "reader-key"})
    assert forbidden.status_code == 403

    listed = client.get("/api/eval/runs", headers={"X-API-Key": "admin-key"})
    assert listed.status_code == 200, listed.text
    runs = listed.json()["runs"]
    assert any(r["run_id"] == run_body["run_id"] for r in runs)
    run_summary = next(r for r in runs if r["run_id"] == run_body["run_id"])
    assert run_summary["dataset_name"] == str(dataset_path)
    assert run_summary["summary"]["examples"] == 1
    assert "diff_from_prev" in run_summary

    detail = client.get(f"/api/eval/runs/{run_body['run_id']}", headers={"X-API-Key": "admin-key"})
    assert detail.status_code == 200, detail.text
    detail_body = detail.json()
    assert detail_body["run"]["run_id"] == run_body["run_id"]
    assert len(detail_body["details"]) == 1
    assert detail_body["details"][0]["case_id"] == "eval-001"


def test_eval_run_diff_tracks_improvements_against_previous_run(tmp_path: Path) -> None:
    main = _reload_app(str(tmp_path / "eval_run_diff.sqlite"))
    client = TestClient(main.app)

    ingest = client.post(
        "/api/ingest/text",
        headers={"X-API-Key": "admin-key"},
        json={
            "title": "Diff Doc",
            "source": "unit-test",
            "text": "Cloud SQL is a managed PostgreSQL service.",
        },
    )
    assert ingest.status_code == 200, ingest.text
    doc_id = str(ingest.json()["doc_id"])

    dataset_path = tmp_path / "datasets" / "diff_eval.jsonl"

    # First run: intentionally unmatchable expected doc id -> fail.
    _write_dataset(
        dataset_path,
        [
            {
                "id": "diff-001",
                "question": "What is Cloud SQL?",
                "expected_doc_ids": ["missing-doc-id"],
            }
        ],
    )
    run1 = client.post(
        "/api/eval/run",
        headers={"X-API-Key": "admin-key"},
        json={"golden_path": str(dataset_path), "k": 3, "include_details": True},
    )
    assert run1.status_code == 200, run1.text
    run1_id = str(run1.json()["run_id"])

    # Second run: same dataset path, fixed expectation -> improvement.
    _write_dataset(
        dataset_path,
        [
            {
                "id": "diff-001",
                "question": "What is Cloud SQL?",
                "expected_doc_ids": [doc_id],
            }
        ],
    )
    run2 = client.post(
        "/api/eval/run",
        headers={"X-API-Key": "admin-key"},
        json={"golden_path": str(dataset_path), "k": 3, "include_details": True},
    )
    assert run2.status_code == 200, run2.text
    run2_id = str(run2.json()["run_id"])

    detail2 = client.get(f"/api/eval/runs/{run2_id}", headers={"X-API-Key": "admin-key"})
    assert detail2.status_code == 200, detail2.text
    run2_detail = detail2.json()["run"]

    assert run2_detail["diff_from_prev"]["previous_run_id"] == run1_id
    assert run2_detail["diff_from_prev"]["case_changes"]["improvements"] >= 1
    assert run2_detail["diff_from_prev"]["case_changes"]["regressions"] == 0
