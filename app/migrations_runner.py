from __future__ import annotations

import time
from pathlib import Path
from typing import Any

_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  filename TEXT PRIMARY KEY,
  applied_at BIGINT NOT NULL
);
"""


def apply_postgres_migrations(conn: Any, *, migrations_dir: Path | None = None) -> list[str]:
    """Apply Postgres SQL migrations in filename order.

    - Uses a simple schema_migrations table (filename -> applied_at).
    - Each migration file should be idempotent and safe to rerun, but we still track applied files.

    Returns a list of newly-applied migration filenames (in order).
    """

    migrations_dir = migrations_dir or (Path(__file__).resolve().parent / "migrations" / "postgres")
    files = sorted([p for p in migrations_dir.glob("*.sql") if p.is_file()])
    if not files:
        return []

    applied: set[str] = set()
    with conn.cursor() as cur:
        cur.execute(_MIGRATIONS_TABLE_SQL)
        cur.execute("SELECT filename FROM schema_migrations")
        rows = cur.fetchall()
        applied = {str(r["filename"]) for r in rows}

        newly: list[str] = []
        for path in files:
            name = path.name
            if name in applied:
                continue
            sql = path.read_text(encoding="utf-8")
            # Execute entire file as one command string (Postgres supports multi-statement strings).
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (filename, applied_at) VALUES (%s, %s)",
                (name, int(time.time())),
            )
            newly.append(name)

    conn.commit()
    return newly
