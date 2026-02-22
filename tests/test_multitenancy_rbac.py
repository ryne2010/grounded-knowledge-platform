from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient


_ENV_KEYS = [
    "SQLITE_PATH",
    "PUBLIC_DEMO_MODE",
    "AUTH_MODE",
    "API_KEYS_JSON",
    "ALLOW_UPLOADS",
    "ALLOW_DOC_DELETE",
    "ALLOW_CHUNK_VIEW",
    "ALLOW_EVAL",
    "BOOTSTRAP_DEMO_CORPUS",
    "CITATIONS_REQUIRED",
]


@pytest.fixture(autouse=True)
def _restore_env_after_test():
    before = {k: os.environ.get(k) for k in _ENV_KEYS}
    yield
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
            continue
        os.environ[key] = value


def _reload_app(sqlite_path: str) -> object:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "api_key"
    os.environ["API_KEYS_JSON"] = (
        '{'
        '"reader-a": {"role": "reader", "tenants": ["tenant-a"]},'
        '"editor-a": {"role": "editor", "tenants": ["tenant-a"]},'
        '"admin-a": {"role": "admin", "tenants": ["tenant-a"]},'
        '"reader-b": {"role": "reader", "tenants": ["tenant-b"]},'
        '"admin-b": {"role": "admin", "tenants": ["tenant-b"]}'
        '}'
    )
    os.environ["ALLOW_UPLOADS"] = "1"
    os.environ["ALLOW_DOC_DELETE"] = "1"
    os.environ["ALLOW_CHUNK_VIEW"] = "1"
    os.environ["ALLOW_EVAL"] = "1"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"
    os.environ["CITATIONS_REQUIRED"] = "1"

    import app.auth as auth
    import app.config as config
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage
    import app.tenant as tenant

    importlib.reload(config)
    importlib.reload(tenant)
    importlib.reload(auth)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(main)
    return main


def _headers(api_key: str, tenant_id: str) -> dict[str, str]:
    return {"X-API-Key": api_key, "X-Tenant-ID": tenant_id}


def test_cross_tenant_isolation_blocks_doc_and_search_access(tmp_path):
    main = _reload_app(str(tmp_path / "multitenant_isolation.sqlite"))
    client = TestClient(main.app)

    ingest_a = client.post(
        "/api/ingest/text",
        headers=_headers("admin-a", "tenant-a"),
        json={
            "title": "Tenant A Doc",
            "source": "unit-test",
            "text": "alpha only policy term tenant-a-secret",
        },
    )
    assert ingest_a.status_code == 200, ingest_a.text

    ingest_b = client.post(
        "/api/ingest/text",
        headers=_headers("admin-b", "tenant-b"),
        json={
            "title": "Tenant B Doc",
            "source": "unit-test",
            "text": "beta only policy term tenant-b-secret",
        },
    )
    assert ingest_b.status_code == 200, ingest_b.text
    doc_b_id = ingest_b.json()["doc_id"]

    # Tenant A cannot fetch tenant B doc detail by id.
    detail = client.get(f"/api/docs/{doc_b_id}", headers=_headers("reader-a", "tenant-a"))
    assert detail.status_code == 404

    # Tenant-scoped search should not leak tenant B chunks into tenant A.
    search_a = client.get(
        "/api/search/chunks",
        headers=_headers("reader-a", "tenant-a"),
        params={"q": "tenant-b-secret", "limit": 10},
    )
    assert search_a.status_code == 200, search_a.text
    assert search_a.json()["results"] == []

    search_b = client.get(
        "/api/search/chunks",
        headers=_headers("reader-b", "tenant-b"),
        params={"q": "tenant-b-secret", "limit": 10},
    )
    assert search_b.status_code == 200, search_b.text
    assert len(search_b.json()["results"]) >= 1


def test_rbac_is_enforced_with_tenant_scoped_api_keys(tmp_path):
    main = _reload_app(str(tmp_path / "multitenant_rbac.sqlite"))
    client = TestClient(main.app)

    # Reader role is enforced inside an allowed tenant.
    reader_ingest = client.post(
        "/api/ingest/text",
        headers=_headers("reader-a", "tenant-a"),
        json={"title": "Reader Blocked", "source": "unit-test", "text": "nope"},
    )
    assert reader_ingest.status_code == 403
    assert "editor role required" in reader_ingest.text

    # Tenant grants are enforced before role checks.
    denied_tenant = client.get("/api/docs", headers=_headers("reader-a", "tenant-b"))
    assert denied_tenant.status_code == 403
    assert "Tenant access denied" in denied_tenant.text

    ingest_editor = client.post(
        "/api/ingest/text",
        headers=_headers("editor-a", "tenant-a"),
        json={"title": "Editor Allowed", "source": "unit-test", "text": "editor can ingest"},
    )
    assert ingest_editor.status_code == 200, ingest_editor.text
    doc_id = ingest_editor.json()["doc_id"]

    delete_wrong_tenant = client.delete(f"/api/docs/{doc_id}", headers=_headers("admin-a", "tenant-b"))
    assert delete_wrong_tenant.status_code == 403
    assert "Tenant access denied" in delete_wrong_tenant.text

    delete_ok = client.delete(f"/api/docs/{doc_id}", headers=_headers("admin-a", "tenant-a"))
    assert delete_ok.status_code == 200, delete_ok.text
    assert delete_ok.json().get("deleted") is True
