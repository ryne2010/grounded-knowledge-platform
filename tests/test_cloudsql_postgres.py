from __future__ import annotations

import hashlib
import os
import socket
import subprocess
import time
import uuid
from pathlib import Path

import numpy as np
import pytest

from app.storage_repo.postgres_adapter import PostgresRepository


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


def _wait_for_postgres(url: str, timeout_s: float = 30.0) -> bool:
    try:
        import psycopg
    except Exception:
        return False
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with psycopg.connect(url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def test_postgres_repository_ingest_query_delete():
    if not _docker_available():
        pytest.skip("docker is not available")
    try:
        import psycopg  # noqa: F401
    except Exception:
        pytest.skip("psycopg is not installed")

    host_port = _free_port()
    container = f"gkp-pg-{uuid.uuid4().hex[:8]}"
    image = os.getenv("GKP_POSTGRES_IMAGE", "pgvector/pgvector:0.8.0-pg16-bookworm")

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

    url = f"postgresql://postgres:postgres@127.0.0.1:{host_port}/gkp"
    try:
        if not _wait_for_postgres(url, timeout_s=45.0):
            pytest.fail("postgres container did not become ready")

        repo = PostgresRepository(url)
        repo.init_schema()

        import psycopg

        migrations_dir = Path(__file__).resolve().parents[1] / "app" / "migrations" / "postgres"
        expected_migrations = sorted(path.name for path in migrations_dir.glob("*.sql"))
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT filename FROM schema_migrations ORDER BY filename ASC")
                applied_migrations = [str(r[0]) for r in cur.fetchall()]
                assert applied_migrations == expected_migrations

                cur.execute(
                    """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname IN ('idx_chunks_fts', 'idx_embeddings_vec_hnsw')
                    """
                )
                idx_defs = {str(r[0]): str(r[1]).lower() for r in cur.fetchall()}
                assert "idx_chunks_fts" in idx_defs
                assert "using gin" in idx_defs["idx_chunks_fts"]
                assert "idx_embeddings_vec_hnsw" in idx_defs
                assert "using hnsw" in idx_defs["idx_embeddings_vec_hnsw"]
                assert "vector_cosine_ops" in idx_defs["idx_embeddings_vec_hnsw"]

        text = "Cloud Run provides managed containers with automatic scaling."
        vec = np.ones((8,), dtype=np.float32).tobytes()
        repo.ingest_document(
            doc_id="pg-doc-1",
            title="Cloud SQL Doc",
            source="integration-test",
            content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            chunks=[text],
            embedding_dim=8,
            embeddings=[vec],
        )

        counts = repo.counts()
        assert counts.docs == 1
        assert counts.chunks == 1
        assert counts.embeddings == 1
        assert counts.ingest_events == 1

        cites = repo.query_citations("managed containers", top_k=3)
        assert len(cites) >= 1
        assert cites[0].doc_id == "pg-doc-1"

        repo.delete_doc("pg-doc-1")
        after = repo.counts()
        assert after.docs == 0
        assert after.chunks == 0
        assert after.embeddings == 0
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
