from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Callable, Literal

from fastapi import HTTPException, Request

from .config import settings

Role = Literal["reader", "editor", "admin"]
AuthMode = Literal["none", "api_key", "oidc"]

_ROLE_RANK: dict[Role, int] = {
    "reader": 1,
    "editor": 2,
    "admin": 3,
}

_HEALTH_PATHS = {"/health", "/ready"}


@dataclass(frozen=True)
class AuthContext:
    principal: str
    role: Role
    mode: AuthMode
    authenticated: bool


@dataclass(frozen=True)
class AuthError(Exception):
    status_code: int
    detail: str


def _normalize_role(value: str | None, default: Role = "reader") -> Role:
    if value is None:
        return default
    raw = value.strip().lower()
    if raw in _ROLE_RANK:
        return raw  # type: ignore[return-value]
    return default


def _mask_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "***"
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:8]
    return f"{api_key[:4]}...{digest}"


def _parse_api_keys_json(raw: str) -> dict[str, Role]:
    try:
        data = json.loads(raw)
    except Exception:
        return {}

    out: dict[str, Role] = {}
    if isinstance(data, dict):
        for key, role in data.items():
            k = str(key).strip()
            if not k:
                continue
            out[k] = _normalize_role(str(role), default="reader")
        return out

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            out[key] = _normalize_role(str(item.get("role", "reader")), default="reader")
    return out


def _parse_api_keys(raw: str) -> dict[str, Role]:
    out: dict[str, Role] = {}
    for token in raw.split(","):
        t = token.strip()
        if not t:
            continue
        if ":" in t:
            key, role = t.split(":", 1)
            k = key.strip()
            if not k:
                continue
            out[k] = _normalize_role(role, default="reader")
            continue
        if "=" in t:
            key, role = t.split("=", 1)
            k = key.strip()
            if not k:
                continue
            out[k] = _normalize_role(role, default="reader")
            continue
        out[t] = "reader"
    return out


def _api_key_role_map() -> dict[str, Role]:
    # Priority:
    # 1) API_KEYS_JSON (explicit key->role map)
    # 2) API_KEYS (comma-separated; supports optional key:role)
    # 3) API_KEY (single key; defaults to admin for operator convenience)
    mapped = _parse_api_keys_json(os.getenv("API_KEYS_JSON", ""))
    if mapped:
        return mapped

    mapped = _parse_api_keys(os.getenv("API_KEYS", ""))
    if mapped:
        return mapped

    single = (os.getenv("API_KEY") or "").strip()
    if not single:
        return {}
    return {single: "admin"}


def effective_auth_mode() -> AuthMode:
    # Public demo mode is always anonymous + read-only regardless of AUTH_MODE.
    if settings.public_demo_mode:
        return "none"
    raw = (os.getenv("AUTH_MODE") or "none").strip().lower()
    if raw in {"none", "api_key", "oidc"}:
        return raw  # type: ignore[return-value]
    return "none"


def resolve_auth_context(request: Request) -> AuthContext:
    mode = effective_auth_mode()
    path = request.url.path

    if mode == "none":
        # Keep current private-mode behavior unchanged when auth is disabled.
        return AuthContext(principal="anonymous", role="admin", mode="none", authenticated=False)

    # Keep health checks unauthenticated so Cloud Run probes continue to work.
    if path in _HEALTH_PATHS:
        return AuthContext(principal="anonymous", role="reader", mode=mode, authenticated=False)

    if mode == "oidc":
        raise AuthError(status_code=501, detail="AUTH_MODE=oidc is not implemented in this build")

    # api_key mode
    key = (request.headers.get("x-api-key") or "").strip()
    if not key:
        raise AuthError(status_code=401, detail="Missing API key")

    role_map = _api_key_role_map()
    if not role_map:
        raise AuthError(status_code=500, detail="AUTH_MODE=api_key requires API_KEYS_JSON, API_KEYS, or API_KEY")

    role = role_map.get(key)
    if role is None:
        raise AuthError(status_code=401, detail="Invalid API key")

    return AuthContext(
        principal=f"api_key:{_mask_key(key)}",
        role=role,
        mode="api_key",
        authenticated=True,
    )


def _ensure_ctx(request: Request) -> AuthContext:
    existing = getattr(request.state, "auth_context", None)
    if isinstance(existing, AuthContext):
        return existing
    ctx = resolve_auth_context(request)
    request.state.auth_context = ctx
    request.state.principal = ctx.principal
    request.state.role = ctx.role
    return ctx


def require_role(required: Role) -> Callable[[Request], AuthContext]:
    def _dep(request: Request) -> AuthContext:
        try:
            ctx = _ensure_ctx(request)
        except AuthError as e:
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e

        if _ROLE_RANK.get(ctx.role, 0) < _ROLE_RANK[required]:
            raise HTTPException(status_code=403, detail=f"{required} role required")
        return ctx

    return _dep
