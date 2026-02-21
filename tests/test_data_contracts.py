from __future__ import annotations

import importlib
import os


def _reload_for_db(sqlite_path: str):
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["SQLITE_PATH"] = sqlite_path

    import app.config as config
    import app.ingestion as ingestion
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(ingestion)
    return ingestion, storage


def test_tabular_contract_happy_path_records_validation(tmp_path):
    db = tmp_path / "contracts_ok.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    csv_path = tmp_path / "events.csv"
    csv_path.write_text("event_id,occurred_at,lat\nabc,2026-01-01T10:00:00,1.2\n", encoding="utf-8")

    contract = """
version: 1
name: customer_events
owner: data-platform
columns:
  - name: event_id
    type: string
    required: true
  - name: occurred_at
    type: timestamp
    required: true
checks:
  min_rows: 1
  max_null_fraction:
    occurred_at: 0.0
""".strip()

    res = ingestion.ingest_file(
        csv_path,
        title="Events",
        source="unit-test",
        contract_bytes=contract.encode("utf-8"),
    )
    assert res.doc_id

    with storage.connect(str(db)) as conn:
        events = storage.list_ingest_events(conn, res.doc_id, limit=1)
        assert events
        evt = events[0]
        assert evt.validation_status == "pass"
        assert evt.schema_fingerprint
        assert evt.contract_sha256
        assert evt.validation_errors == []


def test_tabular_contract_missing_required_column_fails(tmp_path):
    db = tmp_path / "contracts_missing.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    csv_path = tmp_path / "events_missing.csv"
    csv_path.write_text("event_id,lat\nabc,1.2\n", encoding="utf-8")

    contract = """
version: 1
name: customer_events
columns:
  - name: event_id
    type: string
    required: true
  - name: occurred_at
    type: timestamp
    required: true
""".strip()

    try:
        ingestion.ingest_file(
            csv_path,
            title="Events Missing",
            source="unit-test",
            contract_bytes=contract.encode("utf-8"),
        )
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Missing required columns" in str(e)


def test_tabular_contract_invalid_type_fails_with_clear_error(tmp_path):
    db = tmp_path / "contracts_type_mismatch.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    csv_path = tmp_path / "events_type_mismatch.csv"
    csv_path.write_text("event_id,occurred_at\nabc,not-a-timestamp\n", encoding="utf-8")

    contract = """
version: 1
name: customer_events
columns:
  - name: event_id
    type: string
    required: true
  - name: occurred_at
    type: timestamp
    required: true
""".strip()

    try:
        ingestion.ingest_file(
            csv_path,
            title="Events Type Mismatch",
            source="unit-test",
            contract_bytes=contract.encode("utf-8"),
        )
        assert False, "expected ValueError"
    except ValueError as e:
        msg = str(e)
        assert "occurred_at" in msg
        assert "expected type `timestamp`" in msg


def test_tabular_schema_drift_is_recorded(tmp_path):
    db = tmp_path / "contracts_drift.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    first = tmp_path / "first.csv"
    first.write_text("id,amount\n1,10\n", encoding="utf-8")
    second = tmp_path / "second.csv"
    second.write_text("id,amount,currency\n1,10,USD\n", encoding="utf-8")

    res1 = ingestion.ingest_file(first, title="Ledger", source="unit-test")
    res2 = ingestion.ingest_file(second, title="Ledger", source="unit-test")
    assert res1.doc_id == res2.doc_id

    with storage.connect(str(db)) as conn:
        events = storage.list_ingest_events(conn, res2.doc_id, limit=1)
        assert events
        latest = events[0]
        assert latest.schema_drifted_bool is True


def test_tabular_contract_parse_failure_returns_clear_error(tmp_path):
    db = tmp_path / "contracts_bad_parse.sqlite"
    ingestion, storage = _reload_for_db(str(db))

    with storage.connect(str(db)) as conn:
        storage.init_db(conn)

    csv_path = tmp_path / "events_bad_contract.csv"
    csv_path.write_text("event_id,occurred_at\nabc,2026-01-01T10:00:00\n", encoding="utf-8")

    bad_contract = b"version: 1\nname: [\n"
    try:
        ingestion.ingest_file(csv_path, title="Bad Contract", source="unit-test", contract_bytes=bad_contract)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Invalid contract YAML" in str(e)
