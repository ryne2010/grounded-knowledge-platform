from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib import error, request


DEFAULT_SMOKE_QUESTION = "Why use Cloud SQL for persistence?"


@dataclass(frozen=True)
class HttpResponse:
    status: int
    json_body: Any | None
    text: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    status: int
    detail: str


FetchFn = Callable[[str, str, dict[str, Any] | None, dict[str, str], float], HttpResponse]


def _fetch_http(method: str, url: str, payload: dict[str, Any] | None, headers: dict[str, str], timeout_s: float) -> HttpResponse:
    body: bytes | None = None
    req_headers = dict(headers)
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    req = request.Request(url=url, method=method.upper(), data=body, headers=req_headers)

    raw = ""
    status = 0
    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            status = int(resp.status)
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as e:
        status = int(e.code)
        raw = e.read().decode("utf-8", errors="replace")
    except Exception as e:  # pragma: no cover - network failures are environment-specific
        return HttpResponse(status=0, json_body=None, text=f"{type(e).__name__}: {e}")

    parsed: Any | None = None
    if raw.strip():
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None

    return HttpResponse(status=status, json_body=parsed, text=raw)


def _short_text(value: str, *, max_len: int = 180) -> str:
    text = " ".join((value or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _result(name: str, ok: bool, status: int, detail: str) -> CheckResult:
    return CheckResult(name=name, ok=ok, status=int(status), detail=detail)


def run_smoke(
    *,
    base_url: str,
    question: str,
    timeout_s: float,
    api_key: str | None = None,
    fetch: FetchFn | None = None,
) -> tuple[list[CheckResult], bool]:
    do_fetch = fetch or _fetch_http
    url_base = base_url.rstrip("/")
    headers: dict[str, str] = {}
    if api_key:
        headers["X-API-Key"] = api_key

    checks: list[CheckResult] = []

    def call(name: str, method: str, path: str, payload: dict[str, Any] | None = None) -> HttpResponse:
        url = f"{url_base}{path}"
        return do_fetch(method, url, payload, headers, timeout_s)

    health = call("health", "GET", "/health")
    if health.status == 200 and isinstance(health.json_body, dict) and health.json_body.get("status") == "ok":
        checks.append(_result("GET /health", True, health.status, "status=ok"))
    else:
        checks.append(
            _result(
                "GET /health",
                False,
                health.status,
                f"expected 200 + {{status:ok}}, got body={_short_text(health.text)}",
            )
        )

    ready = call("ready", "GET", "/ready")
    if ready.status == 200 and isinstance(ready.json_body, dict) and bool(ready.json_body.get("ready")) is True:
        checks.append(_result("GET /ready", True, ready.status, "ready=true"))
    else:
        checks.append(
            _result(
                "GET /ready",
                False,
                ready.status,
                f"expected 200 + {{ready:true}}, got body={_short_text(ready.text)}",
            )
        )

    meta = call("meta", "GET", "/api/meta")
    meta_body = meta.json_body if isinstance(meta.json_body, dict) else {}
    meta_required = {"public_demo_mode", "llm_provider", "citations_required", "rate_limit_enabled"}
    missing = sorted([k for k in meta_required if k not in meta_body])
    if meta.status != 200:
        checks.append(
            _result(
                "GET /api/meta",
                False,
                meta.status,
                f"expected 200, got body={_short_text(meta.text)}",
            )
        )
    elif missing:
        checks.append(
            _result(
                "GET /api/meta",
                False,
                meta.status,
                f"missing required keys: {', '.join(missing)}",
            )
        )
    else:
        checks.append(
            _result(
                "GET /api/meta",
                True,
                meta.status,
                (
                    f"public_demo_mode={meta_body.get('public_demo_mode')}, "
                    f"llm_provider={meta_body.get('llm_provider')}, "
                    f"citations_required={meta_body.get('citations_required')}"
                ),
            )
        )

    public_demo_mode = bool(meta_body.get("public_demo_mode"))
    if meta.status == 200 and public_demo_mode:
        demo_ok = (
            meta_body.get("llm_provider") == "extractive"
            and bool(meta_body.get("uploads_enabled")) is False
            and bool(meta_body.get("connectors_enabled")) is False
            and bool(meta_body.get("eval_enabled")) is False
        )
        if demo_ok:
            checks.append(_result("Public demo invariants", True, 200, "extractive-only + uploads/connectors/eval disabled"))
        else:
            checks.append(
                _result(
                    "Public demo invariants",
                    False,
                    200,
                    (
                        "expected extractive-only and disabled uploads/connectors/eval; got "
                        f"llm_provider={meta_body.get('llm_provider')} "
                        f"uploads_enabled={meta_body.get('uploads_enabled')} "
                        f"connectors_enabled={meta_body.get('connectors_enabled')} "
                        f"eval_enabled={meta_body.get('eval_enabled')}"
                    ),
                )
            )

    query = call(
        "query",
        "POST",
        "/api/query",
        payload={"question": question, "top_k": 5},
    )
    query_body = query.json_body if isinstance(query.json_body, dict) else {}

    if query.status != 200:
        checks.append(
            _result(
                "POST /api/query",
                False,
                query.status,
                f"expected 200, got body={_short_text(query.text)}",
            )
        )
    else:
        required_query_keys = {"answer", "refused", "citations", "provider"}
        missing_query = sorted([k for k in required_query_keys if k not in query_body])
        if missing_query:
            checks.append(
                _result(
                    "POST /api/query",
                    False,
                    query.status,
                    f"missing required keys: {', '.join(missing_query)}",
                )
            )
        else:
            checks.append(
                _result(
                    "POST /api/query",
                    True,
                    query.status,
                    f"provider={query_body.get('provider')} refused={query_body.get('refused')} citations={len(query_body.get('citations') or [])}",
                )
            )

    if query.status == 200 and public_demo_mode:
        citations = query_body.get("citations")
        refusal = bool(query_body.get("refused"))
        provider = str(query_body.get("provider") or "")
        query_ok = isinstance(citations, list) and len(citations) > 0 and not refusal and provider == "extractive"
        if query_ok:
            checks.append(
                _result(
                    "Public demo query evidence",
                    True,
                    200,
                    f"citations={len(citations)} provider={provider}",
                )
            )
        else:
            checks.append(
                _result(
                    "Public demo query evidence",
                    False,
                    200,
                    (
                        "expected refused=false, citations>0, provider=extractive; got "
                        f"refused={query_body.get('refused')} "
                        f"citations={len(citations) if isinstance(citations, list) else 'n/a'} "
                        f"provider={query_body.get('provider')}"
                    ),
                )
            )

    ok = all(c.ok for c in checks)
    return checks, ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run post-deploy smoke checks.")
    parser.add_argument("--base-url", required=True, help="Base service URL (for example https://...run.app)")
    parser.add_argument("--question", default=DEFAULT_SMOKE_QUESTION, help="Demo-safe smoke query question.")
    parser.add_argument("--timeout-s", type=float, default=8.0, help="Per-request timeout in seconds.")
    parser.add_argument("--api-key", default=None, help="Optional API key for private deployments.")
    parser.add_argument("--retries", type=int, default=1, help="Retry full smoke suite up to N times on failure.")
    parser.add_argument("--retry-delay-s", type=float, default=2.0, help="Delay between retry attempts.")
    args = parser.parse_args(argv)

    print(f"Smoke target URL: {args.base_url.rstrip('/')}")
    print(f"Smoke query: {args.question}")

    attempts = max(1, int(args.retries))
    last_checks: list[CheckResult] = []
    for idx in range(1, attempts + 1):
        checks, ok = run_smoke(
            base_url=args.base_url,
            question=args.question,
            timeout_s=float(args.timeout_s),
            api_key=args.api_key,
        )
        last_checks = checks
        if ok:
            break
        if idx < attempts:
            time.sleep(max(0.0, float(args.retry_delay_s)))

    passed = sum(1 for c in last_checks if c.ok)
    total = len(last_checks)
    for check in last_checks:
        label = "PASS" if check.ok else "FAIL"
        print(f"[{label}] {check.name}: status={check.status} {check.detail}")

    print(f"Smoke summary: {passed}/{total} checks passed")
    if passed != total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
