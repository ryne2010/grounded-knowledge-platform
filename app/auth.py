from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Callable, Literal

from fastapi import HTTPException, Request

from . import config
from .tenant import default_tenant_id, normalize_tenant_id

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
    tenant_id: str


@dataclass(frozen=True)
class AuthError(Exception):
    status_code: int
    detail: str


@dataclass(frozen=True)
class ApiKeyGrant:
    role: Role
    tenants: tuple[str, ...]


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


def _normalize_tenant_scope(raw: object) -> tuple[str, ...]:
    if raw is None:
        return ("*",)

    if isinstance(raw, str):
        token = raw.strip()
        if not token or token == "*":
            return ("*",)
        return (normalize_tenant_id(token),)

    if isinstance(raw, list):
        normalized: set[str] = set()
        for item in raw:
            token = str(item).strip()
            if not token:
                continue
            if token == "*":
                return ("*",)
            normalized.add(normalize_tenant_id(token))
        if not normalized:
            return ("*",)
        return tuple(sorted(normalized))

    return ("*",)


def _parse_grant(value: object) -> ApiKeyGrant:
    if isinstance(value, dict):
        role = _normalize_role(str(value.get("role", "reader")), default="reader")
        tenants = _normalize_tenant_scope(value.get("tenants"))
        return ApiKeyGrant(role=role, tenants=tenants)

    role = _normalize_role(str(value), default="reader")
    return ApiKeyGrant(role=role, tenants=("*",))


def _parse_api_keys_json(raw: str) -> dict[str, ApiKeyGrant]:
    try:
        data = json.loads(raw)
    except Exception:
        return {}

    out: dict[str, ApiKeyGrant] = {}
    if isinstance(data, dict):
        for key, grant in data.items():
            k = str(key).strip()
            if not k:
                continue
            out[k] = _parse_grant(grant)
        return out

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            out[key] = ApiKeyGrant(
                role=_normalize_role(str(item.get("role", "reader")), default="reader"),
                tenants=_normalize_tenant_scope(item.get("tenants")),
            )
    return out


def _parse_api_keys(raw: str) -> dict[str, ApiKeyGrant]:
    out: dict[str, ApiKeyGrant] = {}
    for token in raw.split(","):
        t = token.strip()
        if not t:
            continue
        if ":" in t:
            key, role = t.split(":", 1)
            k = key.strip()
            if not k:
                continue
            out[k] = ApiKeyGrant(role=_normalize_role(role, default="reader"), tenants=("*",))
            continue
        if "=" in t:
            key, role = t.split("=", 1)
            k = key.strip()
            if not k:
                continue
            out[k] = ApiKeyGrant(role=_normalize_role(role, default="reader"), tenants=("*",))
            continue
        out[t] = ApiKeyGrant(role="reader", tenants=("*",))
    return out


def _api_key_grants() -> dict[str, ApiKeyGrant]:
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
    return {single: ApiKeyGrant(role="admin", tenants=("*",))}


def effective_auth_mode() -> AuthMode:
    # Public demo mode is always anonymous + read-only regardless of AUTH_MODE.
    if config.settings.public_demo_mode:
        return "none"
    raw = (os.getenv("AUTH_MODE") or "none").strip().lower()
    if raw in {"none", "api_key", "oidc"}:
        return raw  # type: ignore[return-value]
    return "none"


def _tenant_from_request(request: Request) -> str:
    raw = request.headers.get("x-tenant-id")
    try:
        return normalize_tenant_id(raw)
    except ValueError as e:
        raise AuthError(status_code=400, detail=str(e)) from e


def _grant_allows_tenant(grant: ApiKeyGrant, tenant_id: str) -> bool:
    if "*" in grant.tenants:
        return True
    return tenant_id in grant.tenants


def resolve_auth_context(request: Request) -> AuthContext:
    mode = effective_auth_mode()
    path = request.url.path

    if mode == "none":
        # Keep current private-mode behavior unchanged when auth is disabled.
        return AuthContext(
            principal="anonymous",
            role="admin",
            mode="none",
            authenticated=False,
            tenant_id=default_tenant_id(),
        )

    # Keep health checks unauthenticated so Cloud Run probes continue to work.
    if path in _HEALTH_PATHS:
        return AuthContext(
            principal="anonymous",
            role="reader",
            mode=mode,
            authenticated=False,
            tenant_id=default_tenant_id(),
        )

    if mode == "oidc":
        raise AuthError(status_code=501, detail="AUTH_MODE=oidc is not implemented in this build")

    # api_key mode
    key = (request.headers.get("x-api-key") or "").strip()
    if not key:
        raise AuthError(status_code=401, detail="Missing API key")

    grants = _api_key_grants()
    if not grants:
        raise AuthError(status_code=500, detail="AUTH_MODE=api_key requires API_KEYS_JSON, API_KEYS, or API_KEY")

    grant = grants.get(key)
    if grant is None:
        raise AuthError(status_code=401, detail="Invalid API key")
    tenant_id = _tenant_from_request(request)
    if not _grant_allows_tenant(grant, tenant_id):
        raise AuthError(status_code=403, detail="Tenant access denied")

    return AuthContext(
        principal=f"api_key:{_mask_key(key)}",
        role=grant.role,
        mode="api_key",
        authenticated=True,
        tenant_id=tenant_id,
    )


def _ensure_ctx(request: Request) -> AuthContext:
    existing = getattr(request.state, "auth_context", None)
    if isinstance(existing, AuthContext):
        return existing
    ctx = resolve_auth_context(request)
    request.state.auth_context = ctx
    request.state.principal = ctx.principal
    request.state.role = ctx.role
    request.state.tenant_id = ctx.tenant_id
    return ctx


def require_role(required: Role) -> Callable[[Request], AuthContext]:
    def _dep(request: Request) -> AuthContext:
        try:
            ctx = _ensure_ctx(request)
        except AuthError as e:
            request.state.auth_denied_reason = e.detail
            request.state.auth_denied_status = int(e.status_code)
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e

        if _ROLE_RANK.get(ctx.role, 0) < _ROLE_RANK[required]:
            detail = f"{required} role required"
            request.state.auth_denied_reason = detail
            request.state.auth_denied_status = 403
            raise HTTPException(status_code=403, detail=detail)
        return ctx

    return _dep
