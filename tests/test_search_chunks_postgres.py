from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import app.main as main


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows


class _FakePostgresConn:
    __module__ = "psycopg.fake"

    def __init__(self) -> None:
        self.in_failed_txn = False
        self.rollback_calls = 0

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> _FakeCursor:
        _ = params
        query = " ".join(str(sql).split())

        if "to_tsvector('english', c.text)" in query and "plainto_tsquery('english'" in query:
            # Simulate Postgres FTS query failure that aborts the transaction.
            self.in_failed_txn = True
            raise RuntimeError("fts query failed")

        if "FROM chunks c" in query and "ORDER BY d.updated_at DESC, c.idx ASC" in query:
            if self.in_failed_txn:
                raise RuntimeError("current transaction is aborted")
            return _FakeCursor(
                [
                    {
                        "chunk_id": "doc-1__00001",
                        "doc_id": "doc-1",
                        "idx": 1,
                        "text": "tenant scoped policy content",
                        "doc_title": "Policy",
                        "doc_source": "unit-test",
                        "classification": "internal",
                        "tags_json": '["ops"]',
                    }
                ]
            )

        raise AssertionError(f"Unexpected SQL: {query}")

    def rollback(self) -> None:
        self.in_failed_txn = False
        self.rollback_calls += 1


def test_search_chunks_rolls_back_failed_postgres_search_before_fallback(monkeypatch):
    conn = _FakePostgresConn()

    @contextmanager
    def _fake_connect(_sqlite_path: str):
        yield conn

    monkeypatch.setattr(main, "connect", _fake_connect)
    monkeypatch.setattr(main, "init_db", lambda _conn: None)

    response = main.search_chunks(
        q="tenant policy",
        limit=20,
        _auth=SimpleNamespace(tenant_id="default"),
    )

    assert response.query == "tenant policy"
    assert conn.rollback_calls == 1
    assert len(response.results) == 1
    row = response.results[0]
    assert row.chunk_id == "doc-1__00001"
    assert row.doc_id == "doc-1"
    assert row.tags == ["ops"]
