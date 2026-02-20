from __future__ import annotations

import time

from app.maintenance import find_expired_docs, purge_expired_docs
from app.storage import connect, init_db, list_docs, upsert_doc


def test_retention_purge_dry_run_and_apply(tmp_path) -> None:
    db_path = tmp_path / "retention.sqlite"
    now = int(time.time())

    with connect(str(db_path)) as conn:
        init_db(conn)

        upsert_doc(
            conn,
            doc_id="d1",
            title="Doc 1",
            source="unit-test",
            classification="public",
            retention="30d",
            tags_json='["test"]',
            content_sha256="0" * 64,
            content_bytes=1,
            num_chunks=0,
            doc_version=1,
        )

        upsert_doc(
            conn,
            doc_id="d2",
            title="Doc 2",
            source="unit-test",
            classification="public",
            retention="indefinite",
            tags_json='["test"]',
            content_sha256="1" * 64,
            content_bytes=1,
            num_chunks=0,
            doc_version=1,
        )

        # Force d1 to be older than 30d; d2 should never be auto-purged.
        old_ts = now - (31 * 24 * 60 * 60)
        conn.execute("UPDATE docs SET updated_at=? WHERE doc_id=?", (old_ts, "d1"))
        conn.execute("UPDATE docs SET updated_at=? WHERE doc_id=?", (old_ts, "d2"))
        conn.commit()

        expired = find_expired_docs(conn, now=now)
        assert {d.doc_id for d in expired} == {"d1"}

        # Dry-run should not delete.
        ids_dry = purge_expired_docs(conn, now=now, apply=False)
        assert ids_dry == ["d1"]
        assert {d.doc_id for d in list_docs(conn)} == {"d1", "d2"}

        # Apply should delete.
        ids_apply = purge_expired_docs(conn, now=now, apply=True)
        assert ids_apply == ["d1"]
        assert {d.doc_id for d in list_docs(conn)} == {"d2"}
