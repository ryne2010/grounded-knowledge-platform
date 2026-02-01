from __future__ import annotations

import argparse
from pathlib import Path

from .eval import run_eval
from .ingestion import ingest_file


def cmd_ingest_folder(folder: str) -> None:
    folder_path = Path(folder)
    if not folder_path.exists():
        raise SystemExit(f"Folder does not exist: {folder}")
    files = sorted([p for p in folder_path.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt", ".pdf"}])
    if not files:
        print("No supported files found (.md/.txt/.pdf).")
        return
    for p in files:
        res = ingest_file(p)
        print(f"Ingested {p.name}: doc_id={res.doc_id} chunks={res.num_chunks} dim={res.embedding_dim}")


def cmd_eval(path: str, k: int) -> None:
    res = run_eval(path, k=k)
    print(f"examples={res.n} hit@{k}={res.hit_at_k:.3f} mrr={res.mrr:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="grounded-kp")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest-folder", help="Ingest all docs in a folder (.md/.txt/.pdf).")
    p_ing.add_argument("folder", type=str)

    p_eval = sub.add_parser("eval", help="Run retrieval evaluation on a JSONL golden set.")
    p_eval.add_argument("golden", type=str)
    p_eval.add_argument("--k", type=int, default=5)

    # --- Safety eval (prompt injection regression) ---
    p_safe = sub.add_parser("safety-eval", help="Run prompt-injection safety regression on a JSONL suite.")
    p_safe.add_argument("suite", help="Path to JSONL safety suite.")
    p_safe.add_argument("--endpoint", default="/api/query", help="Query endpoint path (default: /api/query).")
    p_safe.add_argument("--base", default="http://127.0.0.1:8080", help="API base URL (default: http://127.0.0.1:8080).")
    p_safe.add_argument("--k", type=int, default=5, help="Top-k retrieval (default: 5).")



    args = parser.parse_args()
    if args.cmd == "ingest-folder":
        cmd_ingest_folder(args.folder)
    elif args.cmd == "eval":
        cmd_eval(args.golden, args.k)
    elif args.cmd == "safety-eval":
        from app.safety_eval import run_safety_eval
        ok = run_safety_eval(args.suite, api_base=args.base, endpoint_path=args.endpoint, top_k=args.k)
        raise SystemExit(0 if ok else 2)




if __name__ == "__main__":
    main()
