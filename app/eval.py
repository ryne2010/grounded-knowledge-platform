from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .retrieval import RetrievedChunk, retrieve


@dataclass(frozen=True)
class EvalRetrieved:
    chunk_id: str
    doc_id: str
    idx: int
    score: float
    lexical_score: float
    vector_score: float
    text_preview: str

    @staticmethod
    def from_chunk(c: RetrievedChunk) -> "EvalRetrieved":
        return EvalRetrieved(
            chunk_id=c.chunk_id,
            doc_id=c.doc_id,
            idx=c.idx,
            score=float(c.score),
            lexical_score=float(c.lexical_score),
            vector_score=float(c.vector_score),
            text_preview=(c.text or "")[:240],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "idx": self.idx,
            "score": self.score,
            "lexical_score": self.lexical_score,
            "vector_score": self.vector_score,
            "text_preview": self.text_preview,
        }


@dataclass(frozen=True)
class EvalExample:
    case_id: str
    question: str
    expected_doc_ids: tuple[str, ...]
    expected_chunk_ids: tuple[str, ...]
    status: str
    hit: bool
    rank: int | None
    rr: float
    retrieved: tuple[EvalRetrieved, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "question": self.question,
            "expected_doc_ids": list(self.expected_doc_ids),
            "expected_chunk_ids": list(self.expected_chunk_ids),
            "status": self.status,
            "hit": self.hit,
            "rank": self.rank,
            "rr": self.rr,
            "retrieved": [r.to_dict() for r in self.retrieved],
        }


@dataclass(frozen=True)
class EvalResult:
    n: int
    hit_at_k: float
    mrr: float
    passed: int = 0
    failed: int = 0
    examples: tuple[EvalExample, ...] = ()

    def to_dict(self, *, include_details: bool = False) -> dict[str, object]:
        out: dict[str, object] = {
            "examples": self.n,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": (float(self.passed) / float(self.n)) if self.n > 0 else 0.0,
            "hit_at_k": self.hit_at_k,
            "mrr": self.mrr,
        }
        if include_details:
            out["details"] = [ex.to_dict() for ex in self.examples]
        return out


def run_eval(golden_path: str | Path, *, k: int = 5, include_details: bool = False) -> EvalResult:
    """Run a lightweight retrieval evaluation.

    Input format: JSONL file with rows like:

      {"question": "...", "expected_doc_ids": ["..."], "expected_chunk_ids": ["..."]}

    Evaluation:
      - hit@k: does any expected doc_id OR expected chunk_id appear in top-k
      - MRR: reciprocal rank of first hit
    """

    golden_path = Path(golden_path)
    n = 0
    hits = 0
    rr_sum = 0.0
    examples: list[EvalExample] = []

    for row_idx, line in enumerate(golden_path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        q = str(row.get("question", "")).strip()
        if not q:
            continue
        case_id = str(row.get("id") or f"case-{row_idx + 1:04d}")

        expected_docs = {str(x) for x in row.get("expected_doc_ids", []) if str(x).strip()}
        expected_chunks = {str(x) for x in row.get("expected_chunk_ids", []) if str(x).strip()}

        results = retrieve(q, top_k=k)
        n += 1

        rank: int | None = None
        for i, r in enumerate(results, start=1):
            if expected_chunks and r.chunk_id in expected_chunks:
                rank = i
                break
            if expected_docs and r.doc_id in expected_docs:
                rank = i
                break

        hit = rank is not None
        rr = 0.0
        if rank is not None:
            hits += 1
            rr = 1.0 / float(rank)
            rr_sum += rr

        if include_details:
            examples.append(
                EvalExample(
                    case_id=case_id,
                    question=q,
                    expected_doc_ids=tuple(sorted(expected_docs)),
                    expected_chunk_ids=tuple(sorted(expected_chunks)),
                    status="pass" if hit else "fail",
                    hit=hit,
                    rank=rank,
                    rr=rr,
                    retrieved=tuple(EvalRetrieved.from_chunk(c) for c in results),
                )
            )

    if n == 0:
        return EvalResult(n=0, hit_at_k=0.0, mrr=0.0, passed=0, failed=0, examples=tuple(examples))

    return EvalResult(
        n=n,
        hit_at_k=hits / n,
        mrr=rr_sum / n,
        passed=hits,
        failed=n - hits,
        examples=tuple(examples),
    )
