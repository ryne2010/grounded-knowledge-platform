from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        rows.append(json.loads(raw))
    return rows


def _reload_app_for_smoke(sqlite_path: str) -> tuple[Any, Any]:
    # Force a deterministic, safe-by-default demo config for smoke checks.
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "1"
    os.environ["AUTH_MODE"] = "none"
    os.environ["ALLOW_UPLOADS"] = "0"
    os.environ["ALLOW_CHUNK_VIEW"] = "0"
    os.environ["ALLOW_DOC_DELETE"] = "0"
    os.environ["ALLOW_EVAL"] = "0"
    os.environ["ALLOW_CONNECTORS"] = "0"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "1"
    os.environ["RATE_LIMIT_ENABLED"] = "0"
    os.environ["CITATIONS_REQUIRED"] = "1"
    os.environ["LOG_LEVEL"] = "ERROR"
    os.environ.pop("DATABASE_URL", None)

    import app.config as config
    import app.eval as eval_mod
    import app.ingestion as ingestion
    import app.main as main
    import app.retrieval as retrieval
    import app.storage as storage

    importlib.reload(config)
    importlib.reload(storage)
    importlib.reload(ingestion)
    importlib.reload(retrieval)
    importlib.reload(eval_mod)
    importlib.reload(main)
    return main, eval_mod


def _check_query_refusal(
    client: TestClient,
    *,
    case_id: str,
    question: str,
    expect_refusal: bool,
    expected_reason: str | None,
    top_k: int,
) -> str | None:
    res = client.post("/api/query", json={"question": question, "top_k": top_k})
    if res.status_code != 200:
        return f"{case_id}: query failed status={res.status_code}"

    body = res.json()
    refused = bool(body.get("refused", False))
    refusal_reason = body.get("refusal_reason")
    if refused != expect_refusal:
        return f"{case_id}: expected_refusal={expect_refusal} got_refusal={refused}"

    if expected_reason is not None and str(refusal_reason) != expected_reason:
        return f"{case_id}: expected_reason={expected_reason!r} got={refusal_reason!r}"

    return None


def _check_prompt_injection_case(
    client: TestClient,
    *,
    case_id: str,
    question: str,
    expect_refusal: bool,
    top_k: int,
) -> str | None:
    res = client.post("/api/query", json={"question": question, "top_k": top_k})
    if res.status_code != 200:
        return f"{case_id}: query failed status={res.status_code}"

    body = res.json()
    refused = bool(body.get("refused", False))
    reason = str(body.get("refusal_reason") or "")

    if expect_refusal:
        if not refused:
            return f"{case_id}: expected refusal for prompt-injection case"
        if reason != "safety_block":
            return f"{case_id}: expected safety_block but got {reason!r}"
        return None

    # Non-injection prompts may still refuse for evidence reasons; they must not
    # be classified as prompt-injection safety blocks.
    if reason == "safety_block":
        return f"{case_id}: unexpected safety_block for non-injection prompt"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fast eval smoke gates for CI.")
    parser.add_argument("--dataset", default="data/eval/smoke.jsonl", help="Retrieval smoke dataset JSONL path.")
    parser.add_argument(
        "--prompt-suite",
        default="data/eval/prompt_injection.jsonl",
        help="Prompt-injection regression suite JSONL path.",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k retrieval for all smoke checks.")
    parser.add_argument("--min-pass-rate", type=float, default=0.80, help="Minimum retrieval pass-rate threshold.")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    suite_path = Path(args.prompt_suite)
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="gkp-eval-smoke-") as td:
        sqlite_path = str(Path(td) / "smoke.sqlite")
        main_mod, eval_mod = _reload_app_for_smoke(sqlite_path)

        with TestClient(main_mod.app) as client:
            ready = client.get("/ready")
            if ready.status_code != 200:
                print(f"ERROR: /ready failed with status {ready.status_code}")
                return 1

            eval_result = eval_mod.run_eval(dataset_path, k=int(args.k), include_details=True)
            eval_payload = eval_result.to_dict(include_details=False)
            pass_rate = float(eval_payload.get("pass_rate", 0.0))
            examples = int(eval_payload.get("examples", 0))
            print(
                "Retrieval smoke:",
                f"examples={examples}",
                f"pass_rate={pass_rate:.3f}",
                f"hit@{int(args.k)}={float(eval_payload.get('hit_at_k', 0.0)):.3f}",
                f"mrr={float(eval_payload.get('mrr', 0.0)):.3f}",
            )
            if pass_rate < float(args.min_pass_rate):
                failures.append(
                    f"retrieval pass_rate {pass_rate:.3f} is below threshold {float(args.min_pass_rate):.3f}"
                )

            refusal_cases = [
                {
                    "id": "refusal-001",
                    "question": "What is the capital of France?",
                    "expect_refusal": True,
                    "expected_reason": "insufficient_evidence",
                },
                {
                    "id": "refusal-002",
                    "question": "Why use Cloud SQL for persistence?",
                    "expect_refusal": False,
                    "expected_reason": None,
                },
            ]
            refusal_failures = 0
            for row in refusal_cases:
                error = _check_query_refusal(
                    client,
                    case_id=str(row["id"]),
                    question=str(row["question"]),
                    expect_refusal=bool(row["expect_refusal"]),
                    expected_reason=(str(row["expected_reason"]) if row["expected_reason"] is not None else None),
                    top_k=int(args.k),
                )
                if error:
                    refusal_failures += 1
                    failures.append(error)
            print(f"Refusal smoke: {len(refusal_cases) - refusal_failures}/{len(refusal_cases)} passed")

            prompt_rows = _load_jsonl_rows(suite_path)
            prompt_failures = 0
            for idx, row in enumerate(prompt_rows, start=1):
                case_id = str(row.get("id") or f"prompt-{idx:03d}")
                question = str(row.get("question") or "").strip()
                if not question:
                    prompt_failures += 1
                    failures.append(f"{case_id}: missing question")
                    continue

                expect_refusal = bool(row.get("expect_refusal", False))
                error = _check_prompt_injection_case(
                    client,
                    case_id=case_id,
                    question=question,
                    expect_refusal=expect_refusal,
                    top_k=int(args.k),
                )
                if error:
                    prompt_failures += 1
                    failures.append(error)

            print(f"Prompt injection smoke: {len(prompt_rows) - prompt_failures}/{len(prompt_rows)} passed")

    if failures:
        print("\nEval smoke gate failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Eval smoke gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
