from __future__ import annotations

import importlib
import os
import socket
import subprocess
import time
import uuid

import pytest
from fastapi.testclient import TestClient


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _docker_available() -> bool:
    try:
        subprocess.run(["docker", "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _wait_for_postgres(url: str, timeout_s: float = 45.0) -> bool:
    try:
        import psycopg  # noqa: F401
    except Exception:
        return False

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            import psycopg

            with psycopg.connect(url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _reload_app(database_url: str, sqlite_path: str) -> object:
    os.environ["DATABASE_URL"] = database_url
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["CITATIONS_REQUIRED"] = "1"

    import app.config as config
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def test_runtime_uses_postgres_when_database_url_is_set(tmp_path):
    if not _docker_available():
        pytest.skip("docker is not available")

    try:
        import psycopg  # noqa: F401
    except Exception:
        pytest.skip("psycopg is not installed")

    host_port = _free_port()
    container = f"gkp-runtime-pg-{uuid.uuid4().hex[:8]}"
    image = os.getenv("GKP_POSTGRES_IMAGE", "postgres:16-alpine")
    run_cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        container,
        "-e",
        "POSTGRES_PASSWORD=postgres",
        "-e",
        "POSTGRES_DB=gkp",
        "-p",
        f"{host_port}:5432",
        image,
    ]
    subprocess.run(run_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    database_url = f"postgresql://postgres:postgres@127.0.0.1:{host_port}/gkp"
    sqlite_path = str(tmp_path / "should_not_be_used.sqlite")
    prev_database_url = os.environ.get("DATABASE_URL")

    try:
        if not _wait_for_postgres(database_url):
            pytest.fail("postgres container did not become ready")

        main = _reload_app(database_url, sqlite_path)
        client = TestClient(main.app)

        meta = client.get("/api/meta")
        assert meta.status_code == 200, meta.text
        assert meta.json().get("database_backend") == "postgres"

        ingest = client.post(
            "/api/ingest/text",
            json={
                "title": "Runtime PG",
                "source": "integration-test",
                "text": "Cloud SQL provides managed PostgreSQL on GCP.",
            },
        )
        assert ingest.status_code == 200, ingest.text
        doc_id = ingest.json()["doc_id"]

        docs = client.get("/api/docs")
        assert docs.status_code == 200, docs.text
        assert any(d["doc_id"] == doc_id for d in docs.json().get("docs", []))

        query = client.post("/api/query", json={"question": "What does Cloud SQL provide?", "top_k": 3})
        assert query.status_code == 200, query.text
        body = query.json()
        assert body.get("refused") is False
        assert len(body.get("citations", [])) >= 1
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if prev_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev_database_url
