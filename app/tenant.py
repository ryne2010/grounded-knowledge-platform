from __future__ import annotations

import re
from contextvars import ContextVar, Token

_DEFAULT_TENANT_ID = "default"
_TENANT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
_TENANT_DOC_PREFIX_SEP = "::"

_current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default=_DEFAULT_TENANT_ID)


def default_tenant_id() -> str:
    return _DEFAULT_TENANT_ID


def normalize_tenant_id(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if not value:
        return _DEFAULT_TENANT_ID
    if not _TENANT_ID_RE.fullmatch(value):
        raise ValueError("Invalid tenant id")
    return value


def current_tenant_id() -> str:
    return _current_tenant_id.get()


def set_tenant_id(tenant_id: str) -> Token[str]:
    normalized = normalize_tenant_id(tenant_id)
    return _current_tenant_id.set(normalized)


def reset_tenant_id(token: Token[str]) -> None:
    _current_tenant_id.reset(token)


def scope_doc_id(doc_id: str, *, tenant_id: str | None = None) -> str:
    raw = str(doc_id).strip()
    if not raw:
        return raw

    effective_tenant = normalize_tenant_id(tenant_id or current_tenant_id())
    if effective_tenant == _DEFAULT_TENANT_ID:
        return raw

    prefix = f"{effective_tenant}{_TENANT_DOC_PREFIX_SEP}"
    if raw.startswith(prefix):
        return raw
    return f"{prefix}{raw}"
