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

    args = parser.parse_args()
    if args.cmd == "ingest-folder":
        cmd_ingest_folder(args.folder)
    elif args.cmd == "eval":
        cmd_eval(args.golden, args.k)


if __name__ == "__main__":
    main()
