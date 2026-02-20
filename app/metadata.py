from __future__ import annotations

import re

CLASSIFICATIONS: tuple[str, ...] = ("public", "internal", "confidential", "restricted")
RETENTIONS: tuple[str, ...] = ("none", "30d", "90d", "1y", "indefinite")

ALLOWED_CLASSIFICATIONS: set[str] = set(CLASSIFICATIONS)
ALLOWED_RETENTIONS: set[str] = set(RETENTIONS)

_TAG_RE = re.compile(r"[^a-z0-9:_\-]+")


def normalize_classification(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "public"
    v = str(value).strip().lower()
    if v not in ALLOWED_CLASSIFICATIONS:
        raise ValueError(f"Invalid classification: {value!r}. Allowed: {sorted(ALLOWED_CLASSIFICATIONS)}")
    return v


def normalize_retention(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "indefinite"
    v = str(value).strip().lower()
    if v not in ALLOWED_RETENTIONS:
        raise ValueError(f"Invalid retention: {value!r}. Allowed: {sorted(ALLOWED_RETENTIONS)}")
    return v


def normalize_tags(value: str | list[str] | None) -> list[str]:
    tags: list[str] = []
    if value is None:
        return tags

    if isinstance(value, str):
        raw = [t.strip() for t in value.split(",")]
    else:
        raw = [str(t).strip() for t in value]

    for t in raw:
        if not t:
            continue
        t2 = t.lower()
        t2 = _TAG_RE.sub("-", t2).strip("-")
        if not t2:
            continue
        if len(t2) > 32:
            t2 = t2[:32]
        tags.append(t2)

    # de-dupe while preserving order
    out: list[str] = []
    seen: set[str] = set()
    for t in tags:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= 20:
            break

    return out
