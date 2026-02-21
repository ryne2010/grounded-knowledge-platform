from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from ..config import settings
from ..ingestion import ingest_file

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".csv", ".tsv", ".xlsx", ".xlsm"}


@dataclass(frozen=True)
class GCSObject:
    name: str
    size: int
    updated: str | None = None
    generation: str | None = None


def _get_access_token(client: httpx.Client) -> str:
    # Local dev escape hatch (explicit token)
    token = os.getenv("GCP_ACCESS_TOKEN")
    if token:
        return token.strip()

    # Cloud Run / GCE / GKE: use metadata server.
    # https://cloud.google.com/docs/authentication/get-id-token#metadata-server
    url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
    try:
        resp = client.get(url, headers={"Metadata-Flavor": "Google"}, timeout=2.0)
    except Exception as e:
        raise RuntimeError(
            "Unable to reach the GCP metadata server to obtain an access token. "
            "If you're running locally, set GCP_ACCESS_TOKEN (or run the sync via a workload with a service account)."
        ) from e

    if resp.status_code != 200:
        raise RuntimeError(f"Metadata server token request failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    access_token = str(data.get("access_token") or "").strip()
    if not access_token:
        raise RuntimeError("Metadata server response did not include access_token")
    return access_token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def list_objects(
    *,
    bucket: str,
    prefix: str = "",
    max_objects: int | None = None,
    client: httpx.Client,
    token: str,
) -> list[GCSObject]:
    # Cloud Storage JSON API
    url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o"
    out: list[GCSObject] = []
    page_token: str | None = None

    while True:
        params: dict[str, Any] = {"prefix": prefix}
        if page_token:
            params["pageToken"] = page_token

        resp = client.get(url, params=params, headers=_auth_headers(token))
        if resp.status_code != 200:
            raise RuntimeError(f"GCS list failed: {resp.status_code} {resp.text[:200]}")

        body = resp.json()
        for item in body.get("items", []) or []:
            name = str(item.get("name") or "")
            size = int(item.get("size") or 0)
            updated = item.get("updated")
            generation = item.get("generation")
            if name:
                out.append(GCSObject(name=name, size=size, updated=updated, generation=generation))
                if max_objects is not None and len(out) >= max_objects:
                    return out

        page_token = body.get("nextPageToken")
        if not page_token:
            break

    return out


def download_object_to_file(
    *,
    bucket: str,
    name: str,
    dest_path: Path,
    client: httpx.Client,
    token: str,
) -> None:
    encoded = quote(name, safe="")
    url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{encoded}"
    # alt=media returns raw object bytes
    resp = client.get(url, params={"alt": "media"}, headers=_auth_headers(token), follow_redirects=True)
    if resp.status_code != 200:
        raise RuntimeError(f"GCS download failed for gs://{bucket}/{name}: {resp.status_code} {resp.text[:200]}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("wb") as f:
        for chunk in resp.iter_bytes():
            f.write(chunk)


def ingest_object(
    *,
    bucket: str,
    object_name: str,
    generation: str | None = None,
    classification: str | None = None,
    retention: str | None = None,
    tags: str | list[str] | None = None,
    notes: str | None = None,
    run_id: str | None = None,
    expected_size: int | None = None,
) -> dict[str, Any]:
    """Ingest a single GCS object (add/update only).

    This is used by event-driven Pub/Sub push ingestion and shares behavior with
    prefix sync: stable source URI + content hash-based idempotency.
    """

    if settings.public_demo_mode:
        raise RuntimeError("GCS connectors are disabled in PUBLIC_DEMO_MODE")

    bucket_name = str(bucket or "").strip()
    name = str(object_name or "").strip()
    if not bucket_name:
        raise ValueError("bucket is required")
    if not name:
        raise ValueError("object_name is required")

    suffix = Path(name).suffix.lower()
    gcs_uri = f"gs://{bucket_name}/{name}"
    size_hint = int(expected_size) if isinstance(expected_size, int) else 0

    if suffix not in _SUPPORTED_SUFFIXES:
        return {
            "gcs_uri": gcs_uri,
            "action": "skipped_unsupported",
            "size": size_hint,
            "generation": generation,
            "changed": False,
        }

    title = Path(name).name
    safe_base = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).stem)[:120] or "object"
    tmp_dir = Path("/tmp/gkp_gcs_notify")
    tmp_path = tmp_dir / f"{safe_base}_{uuid.uuid4().hex}{suffix}"

    try:
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            token = _get_access_token(client)
            download_object_to_file(bucket=bucket_name, name=name, dest_path=tmp_path, client=client, token=token)

        local_size = int(tmp_path.stat().st_size) if tmp_path.exists() else size_hint
        extra_notes = notes or ""
        connector_notes = json.dumps(
            {"connector": "gcs", "bucket": bucket_name, "name": name, "generation": generation},
            separators=(",", ":"),
        )
        merged_notes = (extra_notes + "\n\n" + connector_notes).strip()

        res = ingest_file(
            tmp_path,
            title=title,
            source=gcs_uri,
            classification=classification,
            retention=retention,
            tags=tags,
            notes=merged_notes,
            run_id=run_id,
        )
        return {
            "gcs_uri": gcs_uri,
            "action": "changed" if res.changed else "unchanged",
            "size": local_size,
            "generation": generation,
            "doc_id": res.doc_id,
            "doc_version": res.doc_version,
            "changed": bool(res.changed),
            "num_chunks": res.num_chunks,
            "content_sha256": res.content_sha256,
        }
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def sync_prefix(
    *,
    bucket: str,
    prefix: str = "",
    max_objects: int = 200,
    dry_run: bool = False,
    classification: str | None = None,
    retention: str | None = None,
    tags: str | list[str] | None = None,
    notes: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Sync documents from a GCS bucket/prefix into the corpus.

    This is designed for **private deployments** and is always disabled in PUBLIC_DEMO_MODE.

    Idempotency:
      - docs use stable_doc_id(title, source) where source is the gs:// URI
      - ingest_events capture content_sha256 so repeated syncs mark unchanged docs

    Returns a run summary dict (safe to return from an API endpoint).
    """

    if settings.public_demo_mode:
        raise RuntimeError("GCS sync is disabled in PUBLIC_DEMO_MODE")

    if max_objects < 1 or max_objects > 5000:
        raise ValueError("max_objects must be between 1 and 5000")

    started_at = int(time.time())
    run_id = run_id or uuid.uuid4().hex

    tmp_dir = Path("/tmp/gkp_gcs_sync")
    scanned = 0
    skipped_unsupported = 0
    ingested = 0
    changed = 0

    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        token = _get_access_token(client)
        objs = list_objects(bucket=bucket, prefix=prefix, max_objects=max_objects, client=client, token=token)

        for obj in objs:
            scanned += 1
            suffix = Path(obj.name).suffix.lower()
            if suffix not in _SUPPORTED_SUFFIXES:
                skipped_unsupported += 1
                continue

            gcs_uri = f"gs://{bucket}/{obj.name}"
            title = Path(obj.name).name
            # Use a safe local filename but keep the original suffix for type detection.
            safe_base = re.sub(r"[^A-Za-z0-9._-]", "_", Path(obj.name).stem)[:120] or "object"
            tmp_path = tmp_dir / f"{safe_base}_{uuid.uuid4().hex}{suffix}"

            if dry_run:
                results.append(
                    {
                        "gcs_uri": gcs_uri,
                        "action": "would_ingest",
                        "size": obj.size,
                        "updated": obj.updated,
                        "generation": obj.generation,
                    }
                )
                continue

            try:
                download_object_to_file(bucket=bucket, name=obj.name, dest_path=tmp_path, client=client, token=token)
                extra_notes = notes or ""
                connector_notes = json.dumps(
                    {"connector": "gcs", "bucket": bucket, "name": obj.name, "generation": obj.generation},
                    separators=(",", ":"),
                )
                merged_notes = (extra_notes + "\n\n" + connector_notes).strip()

                res = ingest_file(
                    tmp_path,
                    title=title,
                    source=gcs_uri,
                    classification=classification,
                    retention=retention,
                    tags=tags,
                    notes=merged_notes,
                    run_id=run_id,
                )
                ingested += 1
                if res.changed:
                    changed += 1
                results.append(
                    {
                        "gcs_uri": gcs_uri,
                        "size": obj.size,
                        "doc_id": res.doc_id,
                        "doc_version": res.doc_version,
                        "changed": res.changed,
                        "num_chunks": res.num_chunks,
                        "content_sha256": res.content_sha256,
                    }
                )
            finally:
                try:
                    tmp_path.unlink()
                except FileNotFoundError:
                    pass

    finished_at = int(time.time())
    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "bucket": bucket,
        "prefix": prefix,
        "dry_run": bool(dry_run),
        "max_objects": int(max_objects),
        "scanned": int(scanned),
        "skipped_unsupported": int(skipped_unsupported),
        "ingested": int(ingested),
        "changed": int(changed),
        "errors": [],
        "results": results,
    }
