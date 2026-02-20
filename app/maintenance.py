"""Operational maintenance helpers.

This module intentionally keeps lifecycle logic (like retention enforcement) out of the
HTTP layer so it can be used by:

- CLI commands (`python -m app.cli ...`)
- future Cloud Scheduler / Cloud Run Jobs integrations

The project stores data in an ephemeral SQLite DB by default when deployed on Cloud Run.
Retention enforcement is therefore mostly relevant for *private* deployments where the
SQLite file is mounted/persisted (or after migrating to Cloud SQL / another store).

Retention semantics in this repo:

- `30d`, `90d`, `1y`: eligible for auto-purge when `updated_at` is older than the policy.
- `none`, `indefinite`: never auto-purged by this command.

This is intentionally conservative: a missing/unknown retention value should never
cause accidental deletion.
"""

from __future__ import annotations

import time
from typing import Iterable

from .storage import Doc, delete_doc, list_docs


RETENTION_TTLS_SECONDS: dict[str, int] = {
    "30d": 30 * 24 * 60 * 60,
    "90d": 90 * 24 * 60 * 60,
    "1y": 365 * 24 * 60 * 60,
}


def iter_expired_docs(docs: Iterable[Doc], *, now: int | None = None) -> list[Doc]:
    """Return the subset of docs whose retention policy has expired."""
    now_i = int(time.time()) if now is None else int(now)
    expired: list[Doc] = []
    for d in docs:
        ttl = RETENTION_TTLS_SECONDS.get(str(d.retention))
        if ttl is None:
            continue
        if int(d.updated_at) <= (now_i - ttl):
            expired.append(d)
    return expired


def find_expired_docs(conn, *, now: int | None = None) -> list[Doc]:
    """Find docs in the DB whose retention policy has expired."""
    return iter_expired_docs(list_docs(conn), now=now)


def purge_expired_docs(conn, *, now: int | None = None, apply: bool = False) -> list[str]:
    """Delete expired docs.

    Returns the list of deleted doc_ids.

    If `apply` is False, no deletes are performed and the function acts as a dry-run.
    """
    expired = find_expired_docs(conn, now=now)
    ids = [d.doc_id for d in expired]
    if not apply:
        return ids

    for doc_id in ids:
        delete_doc(conn, doc_id)
    conn.commit()
    return ids
