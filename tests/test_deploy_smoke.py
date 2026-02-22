from __future__ import annotations

from typing import Any

from scripts.deploy_smoke import HttpResponse, run_smoke


def _path(url: str) -> str:
    marker = "://"
    if marker in url:
        rest = url.split(marker, 1)[1]
        slash = rest.find("/")
        return "/" if slash < 0 else rest[slash:]
    return url


def test_run_smoke_public_demo_success():
    responses: dict[str, HttpResponse] = {
        "/health": HttpResponse(status=200, json_body={"status": "ok"}, text='{"status":"ok"}'),
        "/ready": HttpResponse(status=200, json_body={"ready": True, "version": "x"}, text='{"ready":true}'),
        "/api/meta": HttpResponse(
            status=200,
            json_body={
                "public_demo_mode": True,
                "llm_provider": "extractive",
                "citations_required": True,
                "rate_limit_enabled": True,
                "uploads_enabled": False,
                "connectors_enabled": False,
                "eval_enabled": False,
            },
            text="{}",
        ),
        "/api/query": HttpResponse(
            status=200,
            json_body={
                "answer": "Cloud SQL provides persistent storage.",
                "refused": False,
                "citations": [{"doc_id": "x"}],
                "provider": "extractive",
            },
            text="{}",
        ),
    }

    def fetch(_method: str, url: str, _payload: dict[str, Any] | None, _headers: dict[str, str], _timeout: float) -> HttpResponse:
        return responses[_path(url)]

    checks, ok = run_smoke(
        base_url="https://demo.example.com",
        question="Why use Cloud SQL for persistence?",
        timeout_s=2.0,
        fetch=fetch,
    )

    assert ok is True
    assert all(c.ok for c in checks)


def test_run_smoke_public_demo_fails_when_query_has_no_citations():
    responses: dict[str, HttpResponse] = {
        "/health": HttpResponse(status=200, json_body={"status": "ok"}, text='{"status":"ok"}'),
        "/ready": HttpResponse(status=200, json_body={"ready": True, "version": "x"}, text='{"ready":true}'),
        "/api/meta": HttpResponse(
            status=200,
            json_body={
                "public_demo_mode": True,
                "llm_provider": "extractive",
                "citations_required": True,
                "rate_limit_enabled": True,
                "uploads_enabled": False,
                "connectors_enabled": False,
                "eval_enabled": False,
            },
            text="{}",
        ),
        "/api/query": HttpResponse(
            status=200,
            json_body={
                "answer": "I do not have enough evidence.",
                "refused": True,
                "citations": [],
                "provider": "extractive",
            },
            text="{}",
        ),
    }

    def fetch(_method: str, url: str, _payload: dict[str, Any] | None, _headers: dict[str, str], _timeout: float) -> HttpResponse:
        return responses[_path(url)]

    checks, ok = run_smoke(
        base_url="https://demo.example.com",
        question="Why use Cloud SQL for persistence?",
        timeout_s=2.0,
        fetch=fetch,
    )

    assert ok is False
    assert any((c.name == "Public demo query evidence" and not c.ok) for c in checks)
