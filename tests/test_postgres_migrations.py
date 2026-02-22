from __future__ import annotations

from app.migrations_runner import apply_postgres_migrations


class _FakeCursor:
    def __init__(self, state: dict[str, object]) -> None:
        self._state = state
        self._rows: list[dict[str, str]] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False

    def execute(self, sql: str, params=None) -> None:
        stmt = " ".join((sql or "").strip().split()).lower()
        if stmt.startswith("create table if not exists schema_migrations"):
            return
        if stmt.startswith("select filename from schema_migrations"):
            applied = self._state.get("applied", [])
            self._rows = [{"filename": str(name)} for name in applied if str(name)]
            return
        if stmt.startswith("insert into schema_migrations"):
            if not params:
                raise AssertionError("schema_migrations insert is missing parameters")
            applied = self._state.setdefault("applied", [])
            if not isinstance(applied, list):
                raise AssertionError("invalid fake state: applied must be a list")
            applied.append(str(params[0]))
            return
        executed = self._state.setdefault("executed_sql", [])
        if not isinstance(executed, list):
            raise AssertionError("invalid fake state: executed_sql must be a list")
        executed.append(sql)

    def fetchall(self) -> list[dict[str, str]]:
        return list(self._rows)


class _FakeConn:
    def __init__(self) -> None:
        self.state: dict[str, object] = {"applied": [], "executed_sql": []}
        self.commit_count = 0

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self.state)

    def commit(self) -> None:
        self.commit_count += 1


def test_apply_postgres_migrations_tracks_filenames_in_sorted_order(tmp_path):
    (tmp_path / "010_last.sql").write_text("-- 010_last\nSELECT 10;", encoding="utf-8")
    (tmp_path / "001_init.sql").write_text("-- 001_init\nSELECT 1;", encoding="utf-8")
    (tmp_path / "002_indexes.sql").write_text("-- 002_indexes\nSELECT 2;", encoding="utf-8")

    conn = _FakeConn()

    first = apply_postgres_migrations(conn, migrations_dir=tmp_path)
    assert first == ["001_init.sql", "002_indexes.sql", "010_last.sql"]
    assert conn.state["applied"] == first
    assert conn.state["executed_sql"] == [
        "-- 001_init\nSELECT 1;",
        "-- 002_indexes\nSELECT 2;",
        "-- 010_last\nSELECT 10;",
    ]
    assert conn.commit_count == 1

    second = apply_postgres_migrations(conn, migrations_dir=tmp_path)
    assert second == []
    assert conn.state["applied"] == first
    assert conn.state["executed_sql"] == [
        "-- 001_init\nSELECT 1;",
        "-- 002_indexes\nSELECT 2;",
        "-- 010_last\nSELECT 10;",
    ]
    assert conn.commit_count == 2
