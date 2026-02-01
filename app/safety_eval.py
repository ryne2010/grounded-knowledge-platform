from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import httpx


@dataclass
class CaseResult:
    case_id: str
    ok: bool
    reason: str


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Safety suite not found: {path}")
    rows: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(json.loads(line))
    return rows


def _call_query(
    api_base: str,
    endpoint_path: str,
    question: str,
    top_k: int = 5,
    timeout_s: float = 30.0,
) -> Dict[str, Any]:
    """
    Calls the API query endpoint.

    endpoint_path should be the path portion only, e.g. "/api/query" or "/api/v1/query".
    """
    if not endpoint_path.startswith("/"):
        endpoint_path = "/" + endpoint_path

    url = f"{api_base}{endpoint_path}"
    payload = {"question": question, "top_k": top_k}

    with httpx.Client(timeout=timeout_s) as c:
        r = c.post(url, json=payload)
        # Provide a useful error message if it's not JSON (common for 404/500)
        if r.status_code >= 400:
            body_preview = r.text[:500].replace("\n", "\\n")
            raise RuntimeError(
                f"Query request failed: {r.status_code} {r.reason_phrase}. "
                f"URL={url}. Body preview={body_preview}"
            )
        return r.json()


def run_safety_eval(
    suite_path: str,
    api_base: str = "http://127.0.0.1:8080",
    endpoint_path: str = "/api/query",
    top_k: int = 5,
    timeout_s: float = 30.0,
) -> bool:
    """
    Prompt-injection safety regression runner.

    Expected JSONL format per line (minimal):
      {"id":"pi-001","question":"...","expect_refusal":true}

    Optional fields:
      - expect_contains: ["substring", ...]
      - expect_not_contains: ["substring", ...]
      - notes: "..."
    """
    cases = _load_jsonl(suite_path)
    results: List[CaseResult] = []

    for i, case in enumerate(cases):
        cid = str(case.get("id") or f"case-{i:03d}")
        q = str(case.get("question") or "").strip()
        if not q:
            results.append(CaseResult(cid, False, "missing question"))
            continue

        expect_refusal = bool(case.get("expect_refusal", False))
        expect_contains = list(case.get("expect_contains") or [])
        expect_not_contains = list(case.get("expect_not_contains") or [])

        try:
            resp = _call_query(
                api_base=api_base,
                endpoint_path=endpoint_path,
                question=q,
                top_k=top_k,
                timeout_s=timeout_s,
            )
        except Exception as e:
            results.append(CaseResult(cid, False, f"request failed: {e}"))
            continue

        answer = str(resp.get("answer") or "")
        refused = bool(resp.get("refused", False))

        ok = True
        reason_parts: List[str] = []

        if expect_refusal and not refused:
            ok = False
            reason_parts.append("expected refusal but got answer")
        if (not expect_refusal) and refused:
            ok = False
            reason_parts.append("unexpected refusal")

        for s in expect_contains:
            if s not in answer:
                ok = False
                reason_parts.append(f"missing expected substring: {s!r}")

        for s in expect_not_contains:
            if s in answer:
                ok = False
                reason_parts.append(f"found forbidden substring: {s!r}")

        reason = "; ".join(reason_parts) if reason_parts else "ok"
        results.append(CaseResult(cid, ok, reason))

    total = len(results)
    failed = [r for r in results if not r.ok]
    passed = total - len(failed)

    print(f"Safety eval: {passed}/{total} passed")
    for r in failed[:50]:
        print(f"  FAIL {r.case_id}: {r.reason}")

    return len(failed) == 0
