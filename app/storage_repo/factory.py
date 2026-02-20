from __future__ import annotations

from .postgres_adapter import PostgresRepository
from .sqlite_adapter import SQLiteRepository


def get_repository(*, sqlite_path: str, database_url: str | None):
    if database_url and database_url.startswith("postgres"):
        return PostgresRepository(database_url)
    return SQLiteRepository(sqlite_path)
