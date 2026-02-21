from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path

from .eval import run_eval
from .ingestion import ingest_file, replay_doc


def cmd_ingest_folder(
    folder: str,
    *,
    classification: str | None,
    retention: str | None,
    tags: str | None,
    notes: str | None,
    contract_path: str | None,
) -> None:
    folder_path = Path(folder)
    if not folder_path.exists():
        raise SystemExit(f"Folder does not exist: {folder}")

    supported = {".md", ".txt", ".pdf", ".csv", ".tsv", ".xlsx", ".xlsm"}
    files = sorted([p for p in folder_path.rglob("*") if p.is_file() and p.suffix.lower() in supported])
    if not files:
        print("No supported files found (.md/.txt/.pdf/.csv/.tsv/.xlsx/.xlsm).")
        return

    contract_bytes: bytes | None = None
    if contract_path:
        cp = Path(contract_path)
        if not cp.exists():
            raise SystemExit(f"Contract file does not exist: {contract_path}")
        contract_bytes = cp.read_bytes()

    errors: list[str] = []
    for p in files:
        try:
            use_contract = contract_bytes if p.suffix.lower() in {".csv", ".tsv", ".xlsx", ".xlsm"} else None
            res = ingest_file(
                p,
                classification=classification,
                retention=retention,
                tags=tags,
                notes=notes,
                contract_bytes=use_contract,
            )
            drift = "changed" if res.changed else "unchanged"
            print(
                f"Ingested {p.name}: doc_id={res.doc_id} v{res.doc_version} {drift} "
                f"chunks={res.num_chunks} dim={res.embedding_dim} sha256={res.content_sha256[:10]}…"
            )
        except Exception as e:
            errors.append(f"{p}: {type(e).__name__}: {e}")
            print(f"ERROR ingesting {p.name}: {type(e).__name__}: {e}")

    if errors:
        print("\nOne or more files failed to ingest:")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)


def cmd_ingest_file(
    path: str,
    *,
    title: str | None,
    source: str | None,
    classification: str | None,
    retention: str | None,
    tags: str | None,
    notes: str | None,
    contract_path: str | None,
) -> None:
    file_path = Path(path)
    if not file_path.exists():
        raise SystemExit(f"File does not exist: {path}")

    contract_bytes: bytes | None = None
    if contract_path:
        cp = Path(contract_path)
        if not cp.exists():
            raise SystemExit(f"Contract file does not exist: {contract_path}")
        contract_bytes = cp.read_bytes()

    res = ingest_file(
        file_path,
        title=title,
        source=source,
        classification=classification,
        retention=retention,
        tags=tags,
        notes=notes,
        contract_bytes=contract_bytes,
    )
    drift = "changed" if res.changed else "unchanged"
    print(
        f"Ingested {file_path.name}: doc_id={res.doc_id} v{res.doc_version} {drift} "
        f"chunks={res.num_chunks} dim={res.embedding_dim} sha256={res.content_sha256[:10]}…"
    )


def cmd_eval(path: str, k: int) -> None:
    res = run_eval(path, k=k)
    print(f"examples={res.n} hit@{k}={res.hit_at_k:.3f} mrr={res.mrr:.3f}")


def cmd_retention_sweep(*, apply: bool, now: int | None) -> None:
    """List retention-expired docs and optionally delete them."""
    from .config import settings
    from .maintenance import find_expired_docs, purge_expired_docs, retention_expires_at
    from .storage import connect, init_db, list_docs

    if settings.public_demo_mode:
        raise SystemExit("Retention sweep is disabled in PUBLIC_DEMO_MODE")

    now_i = int(time.time()) if now is None else int(now)
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        total_docs = len(list_docs(conn))
        expired_docs = find_expired_docs(conn, now=now_i)
        deleted_ids: list[str] = purge_expired_docs(conn, now=now_i, apply=True) if apply else []

    mode = "apply" if apply else "dry-run"
    print(f"Retention sweep mode={mode} now={now_i} total_docs={total_docs} expired={len(expired_docs)}")
    if not expired_docs:
        print("No expired docs.")
        return

    for d in expired_docs:
        expires_at = retention_expires_at(str(d.retention), updated_at=int(d.updated_at))
        print(
            f"  - doc_id={d.doc_id} title={d.title!r} retention={d.retention} "
            f"updated_at={int(d.updated_at)} expires_at={expires_at}"
        )

    if apply:
        print(f"Deleted {len(deleted_ids)} doc(s).")
    else:
        print(f"Would delete {len(expired_docs)} doc(s). Re-run with --apply to delete.")


def cmd_purge_expired(*, apply: bool, now: int | None) -> None:
    """Backwards-compatible alias for `retention-sweep`."""
    cmd_retention_sweep(apply=apply, now=now)


def cmd_replay_doc(*, doc_id: str, force: bool) -> None:
    from .config import settings
    from .storage import complete_ingestion_run, connect, create_ingestion_run, init_db

    if settings.public_demo_mode:
        raise SystemExit("Replay/backfill commands are disabled in PUBLIC_DEMO_MODE")

    run_id = uuid.uuid4().hex
    trigger_payload = {"mode": "replay-doc", "doc_id": doc_id, "force": bool(force)}

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        create_ingestion_run(
            conn,
            run_id=run_id,
            trigger_type="cli",
            trigger_payload_json=json.dumps(trigger_payload, ensure_ascii=False),
            principal="cli:replay-doc",
        )
        conn.commit()

    errors: list[str] = []
    docs_changed = 0
    docs_unchanged = 0
    bytes_processed = 0

    try:
        res = replay_doc(doc_id=doc_id, force=force, run_id=run_id)
        if res.changed:
            docs_changed += 1
        else:
            docs_unchanged += 1
        if res.action == "reprocessed":
            bytes_processed += int(res.content_bytes)
    except Exception as e:
        errors.append(f"{doc_id}: {type(e).__name__}: {e}")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        complete_ingestion_run(
            conn,
            run_id=run_id,
            status="failed" if errors else "succeeded",
            objects_scanned=1,
            docs_changed=docs_changed,
            docs_unchanged=docs_unchanged,
            bytes_processed=bytes_processed,
            errors_json=json.dumps(errors, ensure_ascii=False),
        )
        conn.commit()

    if errors:
        print("Replay doc failed:")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)

    action = "reprocessed" if force else "skipped-if-unchanged"
    print(
        f"Replay doc completed: run_id={run_id} doc_id={doc_id} "
        f"mode={action} changed={docs_changed} unchanged={docs_unchanged}"
    )


def cmd_replay_run(*, run_id: str, force: bool) -> None:
    from .config import settings
    from .storage import (
        complete_ingestion_run,
        connect,
        create_ingestion_run,
        get_ingestion_run,
        init_db,
        list_doc_ids_for_run,
    )

    if settings.public_demo_mode:
        raise SystemExit("Replay/backfill commands are disabled in PUBLIC_DEMO_MODE")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        src_run = get_ingestion_run(conn, run_id)
        if src_run is None:
            raise SystemExit(f"Ingestion run not found: {run_id}")
        doc_ids = list_doc_ids_for_run(conn, run_id, limit=10000)

    replay_run_id = uuid.uuid4().hex
    trigger_payload = {
        "mode": "replay-run",
        "source_run_id": run_id,
        "force": bool(force),
        "doc_count": len(doc_ids),
    }
    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        create_ingestion_run(
            conn,
            run_id=replay_run_id,
            trigger_type="cli",
            trigger_payload_json=json.dumps(trigger_payload, ensure_ascii=False),
            principal="cli:replay-run",
        )
        conn.commit()

    errors: list[str] = []
    docs_changed = 0
    docs_unchanged = 0
    bytes_processed = 0

    for doc_id in doc_ids:
        try:
            res = replay_doc(doc_id=doc_id, force=force, run_id=replay_run_id)
            if res.changed:
                docs_changed += 1
            else:
                docs_unchanged += 1
            if res.action == "reprocessed":
                bytes_processed += int(res.content_bytes)
        except Exception as e:
            errors.append(f"{doc_id}: {type(e).__name__}: {e}")

    with connect(settings.sqlite_path) as conn:
        init_db(conn)
        complete_ingestion_run(
            conn,
            run_id=replay_run_id,
            status="failed" if errors else "succeeded",
            objects_scanned=len(doc_ids),
            docs_changed=docs_changed,
            docs_unchanged=docs_unchanged,
            bytes_processed=bytes_processed,
            errors_json=json.dumps(errors, ensure_ascii=False),
        )
        conn.commit()

    if errors:
        print(f"Replay run failed: replay_run_id={replay_run_id} source_run_id={run_id}")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)

    action = "force-reprocess" if force else "skip-if-unchanged"
    print(
        f"Replay run completed: replay_run_id={replay_run_id} source_run_id={run_id} "
        f"docs={len(doc_ids)} mode={action} changed={docs_changed} unchanged={docs_unchanged}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="grounded-kp")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_file = sub.add_parser("ingest-file", help="Ingest one file (.md/.txt/.pdf/.csv/.tsv/.xlsx/.xlsm).")
    p_file.add_argument("path", type=str)
    p_file.add_argument("--title", default=None)
    p_file.add_argument("--source", default=None)
    p_file.add_argument("--classification", default=None, help="public|internal|confidential|restricted")
    p_file.add_argument("--retention", default=None, help="none|30d|90d|1y|indefinite")
    p_file.add_argument("--tags", default=None, help="Comma-separated tags")
    p_file.add_argument("--notes", default=None, help="Optional ingest note")
    p_file.add_argument("--contract", default=None, help="Optional YAML contract for tabular files")

    p_ing = sub.add_parser("ingest-folder", help="Ingest all docs in a folder (.md/.txt/.pdf/.csv/.tsv/.xlsx/.xlsm).")
    p_ing.add_argument("folder", type=str)
    p_ing.add_argument("--classification", default=None, help="public|internal|confidential|restricted")
    p_ing.add_argument("--retention", default=None, help="none|30d|90d|1y|indefinite")
    p_ing.add_argument("--tags", default=None, help="Comma-separated tags")
    p_ing.add_argument("--notes", default=None, help="Optional ingest note")
    p_ing.add_argument("--contract", default=None, help="Optional YAML contract for tabular files")

    p_eval = sub.add_parser("eval", help="Run retrieval evaluation on a JSONL golden set.")
    p_eval.add_argument("golden", type=str)
    p_eval.add_argument("--k", type=int, default=5)

    # --- Safety eval (prompt injection regression) ---
    p_safe = sub.add_parser("safety-eval", help="Run prompt-injection safety regression on a JSONL suite.")
    p_safe.add_argument("suite", help="Path to JSONL safety suite.")
    p_safe.add_argument("--endpoint", default="/api/query", help="Query endpoint path (default: /api/query).")
    p_safe.add_argument(
        "--base", default="http://127.0.0.1:8080", help="API base URL (default: http://127.0.0.1:8080)."
    )
    p_safe.add_argument("--k", type=int, default=5, help="Top-k retrieval (default: 5).")

    # --- Maintenance (retention sweep) ---
    p_sweep = sub.add_parser("retention-sweep", help="List retention-expired docs and optionally delete them.")
    p_sweep.add_argument("--apply", action="store_true", help="Actually delete expired docs (default: dry-run).")
    p_sweep.add_argument("--now", type=int, default=None, help="Override 'now' unix timestamp (testing).")

    p_purge = sub.add_parser("purge-expired", help="Deprecated alias for retention-sweep.")
    p_purge.add_argument("--apply", action="store_true", help="Actually delete expired docs (default: dry-run).")
    p_purge.add_argument("--now", type=int, default=None, help="Override 'now' unix timestamp (testing).")

    # --- Replay / backfill (private deployments only) ---
    p_replay_doc = sub.add_parser("replay-doc", help="Replay one doc safely (skip unchanged unless --force).")
    p_replay_doc.add_argument("--doc-id", required=True, help="Document id to replay.")
    p_replay_doc.add_argument("--force", action="store_true", help="Force re-chunk/re-embed even if unchanged.")

    p_replay_run = sub.add_parser("replay-run", help="Replay all docs linked to an ingestion run.")
    p_replay_run.add_argument("--run-id", required=True, help="Ingestion run id to replay.")
    p_replay_run.add_argument("--force", action="store_true", help="Force re-chunk/re-embed even if unchanged.")

    args = parser.parse_args()
    if args.cmd == "ingest-file":
        cmd_ingest_file(
            args.path,
            title=args.title,
            source=args.source,
            classification=args.classification,
            retention=args.retention,
            tags=args.tags,
            notes=args.notes,
            contract_path=args.contract,
        )
    elif args.cmd == "ingest-folder":
        cmd_ingest_folder(
            args.folder,
            classification=args.classification,
            retention=args.retention,
            tags=args.tags,
            notes=args.notes,
            contract_path=args.contract,
        )
    elif args.cmd == "eval":
        cmd_eval(args.golden, args.k)
    elif args.cmd == "retention-sweep":
        cmd_retention_sweep(apply=bool(args.apply), now=args.now)
    elif args.cmd == "purge-expired":
        cmd_purge_expired(apply=bool(args.apply), now=args.now)
    elif args.cmd == "replay-doc":
        cmd_replay_doc(doc_id=str(args.doc_id), force=bool(args.force))
    elif args.cmd == "replay-run":
        cmd_replay_run(run_id=str(args.run_id), force=bool(args.force))
    elif args.cmd == "safety-eval":
        from app.safety_eval import run_safety_eval

        ok = run_safety_eval(args.suite, api_base=args.base, endpoint_path=args.endpoint, top_k=args.k)
        raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
