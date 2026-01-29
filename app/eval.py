from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .retrieval import retrieve


@dataclass(frozen=True)
class EvalResult:
    n: int
    hit_at_k: float
    mrr: float


def run_eval(golden_path: str | Path, *, k: int = 5) -> EvalResult:
    golden_path = Path(golden_path)
    n = 0
    hits = 0
    rr_sum = 0.0

    for line in golden_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        q = row["question"]
        expected_docs = set(row.get("expected_doc_ids", []))
        expected_chunks = set(row.get("expected_chunk_ids", []))

        results = retrieve(q, top_k=k)
        n += 1

        rank = None
        for i, r in enumerate(results, start=1):
            if expected_chunks and r.chunk_id in expected_chunks:
                rank = i
                break
            if expected_docs and r.doc_id in expected_docs:
                rank = i
                break

        if rank is not None:
            hits += 1
            rr_sum += 1.0 / rank

    if n == 0:
        return EvalResult(n=0, hit_at_k=0.0, mrr=0.0)
    return EvalResult(n=n, hit_at_k=hits / n, mrr=rr_sum / n)
