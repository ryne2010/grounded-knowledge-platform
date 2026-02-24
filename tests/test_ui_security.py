from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_ui_fallback_blocks_path_traversal(tmp_path, monkeypatch):
    # Import lazily so we can monkeypatch DIST_DIR.
    from app import main

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("INDEX", encoding="utf-8")
    (dist / "favicon.svg").write_text("<svg/>", encoding="utf-8")

    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET", encoding="utf-8")

    # Force the module to use our temp dist.
    monkeypatch.setattr(main, "DIST_DIR", Path(dist).resolve())

    # A traversal attempt should never return the secret file.
    resp = main.ui_fallback("../secret.txt")

    # The SPA fallback should serve index.html instead.
    try:
        path = Path(getattr(resp, "path"))
    except Exception:
        pytest.fail("ui_fallback did not return a FileResponse-like object")

    assert path.resolve() == (dist / "index.html").resolve()

    # A normal asset should be served from dist.
    resp2 = main.ui_fallback("favicon.svg")
    path2 = Path(getattr(resp2, "path")).resolve()
    assert path2 == (dist / "favicon.svg").resolve()


def test_swagger_csp_allows_fastapi_default_cdn_assets():
    from app import main

    client = TestClient(main.app)
    resp = client.get("/api/swagger")
    assert resp.status_code == 200
    csp = resp.headers.get("content-security-policy", "")

    # FastAPI's default Swagger UI template references jsDelivr assets.
    assert "https://cdn.jsdelivr.net" in csp
    assert "script-src" in csp
