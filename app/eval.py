from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


@dataclass(frozen=True)
class EvalDatasetValidationResult:
    path: str
    total_cases: int
    answerable_cases: int
    refusal_cases: int
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _read_jsonl_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError(f"line {line_no}: row must be a JSON object")
        rows.append((line_no, payload))
    return rows


def _coerce_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if isinstance(item, str) and str(item).strip()}


def _validate_string_list_field(
    value: Any,
    *,
    line_no: int,
    field: str,
    errors: list[str],
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        errors.append(f"line {line_no}: field '{field}' must be an array of non-empty strings")
        return ()

    out: list[str] = []
    for idx, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"line {line_no}: field '{field}[{idx}]' must be a non-empty string")
            continue
        out.append(item.strip())
    return tuple(out)


def _validate_expectation(row: dict[str, Any], *, line_no: int, errors: list[str]) -> str:
    # Canonical format: {"expect": {"type": "must_cite"|"must_refuse", ...}}
    if "expect" in row:
        expect = row.get("expect")
        if not isinstance(expect, dict):
            errors.append(f"line {line_no}: field 'expect' must be an object")
            return "invalid"
        expect_type = str(expect.get("type", "")).strip()
        if expect_type not in {"must_cite", "must_refuse"}:
            errors.append(f"line {line_no}: field 'expect.type' must be 'must_cite' or 'must_refuse'")
            return "invalid"
        if expect_type == "must_refuse":
            return "must_refuse"
        doc_ids = _validate_string_list_field(expect.get("doc_ids"), line_no=line_no, field="expect.doc_ids", errors=errors)
        chunk_ids = _validate_string_list_field(
            expect.get("chunk_ids"), line_no=line_no, field="expect.chunk_ids", errors=errors
        )
        if not doc_ids and not chunk_ids:
            errors.append(f"line {line_no}: expect.type=must_cite requires non-empty 'expect.doc_ids' or 'expect.chunk_ids'")
            return "invalid"
        return "must_cite"

    # Legacy retrieval format.
    doc_ids = _validate_string_list_field(row.get("expected_doc_ids"), line_no=line_no, field="expected_doc_ids", errors=errors)
    chunk_ids = _validate_string_list_field(
        row.get("expected_chunk_ids"), line_no=line_no, field="expected_chunk_ids", errors=errors
    )
    if doc_ids or chunk_ids:
        return "must_cite"

    # Legacy safety suite format.
    if "expect_refusal" in row:
        expect_refusal = row.get("expect_refusal")
        if not isinstance(expect_refusal, bool):
            errors.append(f"line {line_no}: field 'expect_refusal' must be a boolean")
            return "invalid"
        return "must_refuse" if expect_refusal else "answerable"

    errors.append(
        f"line {line_no}: missing expectation (use 'expect', 'expected_doc_ids'/'expected_chunk_ids', or 'expect_refusal')"
    )
    return "invalid"


def validate_eval_dataset(path: str | Path) -> EvalDatasetValidationResult:
    dataset_path = Path(path)
    errors: list[str] = []
    answerable_cases = 0
    refusal_cases = 0
    total_cases = 0
    seen_case_ids: dict[str, int] = {}

    if not dataset_path.exists():
        return EvalDatasetValidationResult(
            path=str(dataset_path),
            total_cases=0,
            answerable_cases=0,
            refusal_cases=0,
            errors=(f"dataset file not found: {dataset_path}",),
        )

    for line_no, line in enumerate(dataset_path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue

        total_cases += 1
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON ({exc.msg})")
            continue

        if not isinstance(payload, dict):
            errors.append(f"line {line_no}: row must be a JSON object")
            continue

        case_id = payload.get("id")
        if case_id is not None:
            if not isinstance(case_id, str) or not case_id.strip():
                errors.append(f"line {line_no}: field 'id' must be a non-empty string when provided")
            else:
                cid = case_id.strip()
                prev = seen_case_ids.get(cid)
                if prev is not None:
                    errors.append(f"line {line_no}: duplicate id '{cid}' (first seen on line {prev})")
                else:
                    seen_case_ids[cid] = line_no

        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            errors.append(f"line {line_no}: field 'question' is required and must be a non-empty string")

        expectation = _validate_expectation(payload, line_no=line_no, errors=errors)
        if expectation in {"must_cite", "answerable"}:
            answerable_cases += 1
        elif expectation == "must_refuse":
            refusal_cases += 1

    return EvalDatasetValidationResult(
        path=str(dataset_path),
        total_cases=total_cases,
        answerable_cases=answerable_cases,
        refusal_cases=refusal_cases,
        errors=tuple(errors),
    )


def _citation_expectations(row: dict[str, Any]) -> tuple[set[str], set[str]]:
    expect = row.get("expect")
    if isinstance(expect, dict) and str(expect.get("type", "")).strip() == "must_cite":
        return _coerce_string_set(expect.get("doc_ids")), _coerce_string_set(expect.get("chunk_ids"))
    return _coerce_string_set(row.get("expected_doc_ids")), _coerce_string_set(row.get("expected_chunk_ids"))


def run_eval(golden_path: str | Path, *, k: int = 5, include_details: bool = False) -> EvalResult:
    """Run a lightweight retrieval evaluation.

    Input format: JSONL file with rows like:

      {"question": "...", "expected_doc_ids": ["..."], "expected_chunk_ids": ["..."]}

    Evaluation:
      - hit@k: does any expected doc_id OR expected chunk_id appear in top-k
      - MRR: reciprocal rank of first hit
    """

    golden_path = Path(golden_path)
    validation = validate_eval_dataset(golden_path)
    if not validation.ok:
        raise ValueError("invalid eval dataset:\n- " + "\n- ".join(validation.errors))

    n = 0
    hits = 0
    rr_sum = 0.0
    examples: list[EvalExample] = []

    for row_idx, (_line_no, row) in enumerate(_read_jsonl_rows(golden_path)):
        q = str(row.get("question", "")).strip()
        if not q:
            continue
        case_id = str(row.get("id") or f"case-{row_idx + 1:04d}")

        expected_docs, expected_chunks = _citation_expectations(row)
        if not expected_docs and not expected_chunks:
            continue

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
