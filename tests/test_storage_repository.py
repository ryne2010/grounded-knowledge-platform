from __future__ import annotations

import hashlib

import numpy as np

from app.storage_repo.sqlite_adapter import SQLiteRepository


def test_sqlite_repository_ingest_query_delete(tmp_path):
    db_path = tmp_path / "repo.sqlite"
    repo = SQLiteRepository(str(db_path))
    repo.init_schema()

    text = "Cloud Run runs containers and scales to zero."
    vec = np.ones((8,), dtype=np.float32).tobytes()
    repo.ingest_document(
        doc_id="doc-1",
        title="Repo Doc",
        source="unit-test",
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

    cites = repo.query_citations("What runs containers?", top_k=3)
    assert len(cites) >= 1
    assert cites[0].doc_id == "doc-1"

    repo.delete_doc("doc-1")
    after = repo.counts()
    assert after.docs == 0
    assert after.chunks == 0
    assert after.embeddings == 0
