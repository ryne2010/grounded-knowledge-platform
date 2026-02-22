from __future__ import annotations

import importlib
import os

import pytest


_ENV_KEYS = [
    "PUBLIC_DEMO_MODE",
    "AUTH_MODE",
    "BOOTSTRAP_DEMO_CORPUS",
    "EMBEDDINGS_BACKEND",
    "RETRIEVAL_LEXICAL_WEIGHT",
    "RETRIEVAL_VECTOR_WEIGHT",
    "RETRIEVAL_LEXICAL_LIMIT",
    "RETRIEVAL_VECTOR_LIMIT",
    "SQLITE_PATH",
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


def _reload_modules(sqlite_path: str) -> tuple[object, object]:
    os.environ["SQLITE_PATH"] = sqlite_path
    os.environ["PUBLIC_DEMO_MODE"] = "0"
    os.environ["AUTH_MODE"] = "none"
    os.environ["BOOTSTRAP_DEMO_CORPUS"] = "0"

    import app.config as config
    import app.main as main
    import app.retrieval as retrieval

    importlib.reload(config)
    importlib.reload(retrieval)
    importlib.reload(main)
    return retrieval, main


def test_effective_hybrid_weights_normalize_and_fallback(tmp_path):
    os.environ["EMBEDDINGS_BACKEND"] = "hash"
    os.environ["RETRIEVAL_LEXICAL_WEIGHT"] = "3"
    os.environ["RETRIEVAL_VECTOR_WEIGHT"] = "1"
    retrieval, _main = _reload_modules(str(tmp_path / "retrieval_weights.sqlite"))

    lw, vw = retrieval.effective_hybrid_weights(use_vector=True)
    assert lw == pytest.approx(0.75, abs=1e-6)
    assert vw == pytest.approx(0.25, abs=1e-6)

    os.environ["RETRIEVAL_LEXICAL_WEIGHT"] = "0"
    os.environ["RETRIEVAL_VECTOR_WEIGHT"] = "0"
    retrieval, _main = _reload_modules(str(tmp_path / "retrieval_weights_zero.sqlite"))
    lw2, vw2 = retrieval.effective_hybrid_weights(use_vector=True)
    assert lw2 == pytest.approx(0.5, abs=1e-6)
    assert vw2 == pytest.approx(0.5, abs=1e-6)

    lw3, vw3 = retrieval.effective_hybrid_weights(use_vector=False)
    assert lw3 == pytest.approx(1.0, abs=1e-6)
    assert vw3 == pytest.approx(0.0, abs=1e-6)


def test_eval_retrieval_config_uses_runtime_tuning_knobs(tmp_path):
    os.environ["EMBEDDINGS_BACKEND"] = "hash"
    os.environ["RETRIEVAL_LEXICAL_WEIGHT"] = "2"
    os.environ["RETRIEVAL_VECTOR_WEIGHT"] = "1"
    os.environ["RETRIEVAL_LEXICAL_LIMIT"] = "77"
    os.environ["RETRIEVAL_VECTOR_LIMIT"] = "31"

    _retrieval, main = _reload_modules(str(tmp_path / "retrieval_eval_config.sqlite"))
    cfg = main._eval_retrieval_config(k=7)

    assert cfg["k"] == 7
    assert cfg["vector_enabled"] is True
    assert cfg["candidate_limits"] == {"lexical": 77, "vector": 31}
    assert cfg["hybrid_weights"]["lexical"] == pytest.approx(2.0 / 3.0, abs=1e-6)
    assert cfg["hybrid_weights"]["vector"] == pytest.approx(1.0 / 3.0, abs=1e-6)


def test_retrieval_tie_break_sort_is_deterministic(tmp_path):
    os.environ["EMBEDDINGS_BACKEND"] = "hash"
    retrieval, _main = _reload_modules(str(tmp_path / "retrieval_sort.sqlite"))

    rows = [
        retrieval.RetrievedChunk(
            chunk_id="chunk-b",
            doc_id="doc-b",
            idx=2,
            text="beta",
            score=0.5,
            lexical_score=0.5,
            vector_score=0.5,
        ),
        retrieval.RetrievedChunk(
            chunk_id="chunk-a",
            doc_id="doc-a",
            idx=1,
            text="alpha",
            score=0.5,
            lexical_score=0.5,
            vector_score=0.5,
        ),
    ]

    ordered = sorted(rows, key=retrieval._retrieval_sort_key)
    assert [r.chunk_id for r in ordered] == ["chunk-a", "chunk-b"]
