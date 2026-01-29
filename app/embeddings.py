from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import numpy as np

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return shape (n, dim) float32 array."""
        ...


@dataclass
class NoEmbedder:
    """Embeddings disabled.

    Useful for minimal-footprint deployments where lexical retrieval is sufficient.
    """

    dim: int = 1

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.zeros((len(texts), self.dim), dtype=np.float32)


@dataclass
class HashEmbedder:
    """A no-download embedding baseline.

    This is **not** SOTA; it's here so the project runs out of the box without network access or model downloads.
    """

    dim: int = 512

    def embed(self, texts: list[str]) -> np.ndarray:
        mats: list[np.ndarray] = []
        for t in texts:
            v = np.zeros(self.dim, dtype=np.float32)
            for tok in _TOKEN_RE.findall(t.lower()):
                v[hash(tok) % self.dim] += 1.0
            norm = float(np.linalg.norm(v))
            if norm > 0:
                v /= norm
            mats.append(v)
        if not mats:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.stack(mats, axis=0)


class SentenceTransformerEmbedder:
    """Higher-quality embeddings (requires downloading a model)."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.model = SentenceTransformer(model_name)
        try:
            self.dim = int(self.model.get_sentence_embedding_dimension())
        except Exception:
            self.dim = int(self.model.encode(["test"], normalize_embeddings=True).shape[1])

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        arr = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(arr, dtype=np.float32)


def cosine_sim(query_vec: np.ndarray, mat: np.ndarray) -> np.ndarray:
    """Cosine similarity between query vector (dim,) and matrix (n, dim)."""
    if mat.shape[0] == 0:
        return np.zeros((0,), dtype=np.float32)
    q = query_vec.astype(np.float32)
    m = mat.astype(np.float32)
    return m @ q
