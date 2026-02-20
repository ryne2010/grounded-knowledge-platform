#!/usr/bin/env python3
"""Create a clean, shareable source ZIP of the repository.

Why this exists:
- Zipping a working directory after running tests often scoops up caches
  (`__pycache__`, `.pytest_cache`, `.venv`, `node_modules`, etc.).
- This script produces a deterministic-ish archive that includes only
  source + docs + infra, excluding common build artifacts and secrets.

Usage:
  python scripts/package_repo.py            # writes dist/gkp_repo_<version>.zip
  python scripts/package_repo.py --out out.zip

This is designed for local dev on macOS (M2) and CI/CD runners.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path


EXCLUDE_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    "dist",
    ".terraform",
    ".idea",
    ".vscode",
}

# Exclude by filename (not full path).
EXCLUDE_FILE_NAMES = {
    ".DS_Store",
}

# Exclude by glob (matches filename OR posix relpath).
EXCLUDE_GLOBS = [
    "*.pyc",
    "*.pyo",
    "*.sqlite",
    "*.db",
    "*.log",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.jks",
]

# Exclude specific path prefixes (posix style).
EXCLUDE_PATH_PREFIXES = [
    "web/dist/",
    "web/node_modules/",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_version(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return "0.0.0"

    # Python 3.11+: tomllib is stdlib.
    import tomllib  # type: ignore

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(data.get("project", {}).get("version", "0.0.0"))


def _git_rev(root: Path) -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(root), stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None


def _should_exclude(rel_posix: str, path: Path) -> bool:
    # Normalize: ensure directories have trailing slash for prefix matching.
    rel_posix = rel_posix.lstrip("/")

    # Prefix exclusions.
    for pref in EXCLUDE_PATH_PREFIXES:
        if rel_posix.startswith(pref):
            return True

    parts = rel_posix.split("/")
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True

    name = path.name
    if name in EXCLUDE_FILE_NAMES:
        return True

    for pat in EXCLUDE_GLOBS:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_posix, pat):
            return True

    return False


def _iter_files(root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        rel_posix = p.relative_to(root).as_posix()
        if _should_exclude(rel_posix, p):
            continue
        files.append((p, rel_posix))

    # Stable ordering.
    files.sort(key=lambda t: t[1])
    return files


def _zip_write_file(zf: zipfile.ZipFile, src: Path, arcname: str) -> None:
    # Preserve executable bit on POSIX.
    st = src.stat()
    zi = zipfile.ZipInfo(arcname)
    # Preserve modified time (zip stores local time; use UTC-ish tuple for determinism).
    zi.date_time = time.gmtime(st.st_mtime)[:6]
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = (st.st_mode & 0xFFFF) << 16
    zf.writestr(zi, src.read_bytes())


def main() -> int:
    root = _repo_root()
    version = _read_version(root)
    prefix = root.name

    ap = argparse.ArgumentParser(prog="package_repo")
    ap.add_argument("--out", default=str(root / "dist" / f"gkp_repo_{version}.zip"))
    args = ap.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    files = _iter_files(root)

    info = {
        "name": "grounded-knowledge-platform",
        "version": version,
        "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version.split()[0],
        "git_rev": _git_rev(root),
        "file_count": len(files),
        "excludes": {
            "dir_names": sorted(EXCLUDE_DIR_NAMES),
            "file_names": sorted(EXCLUDE_FILE_NAMES),
            "globs": EXCLUDE_GLOBS,
            "path_prefixes": EXCLUDE_PATH_PREFIXES,
        },
    }

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add dist info first.
        zf.writestr(f"{prefix}/DIST_INFO.json", json.dumps(info, indent=2, sort_keys=True))

        for src, rel in files:
            _zip_write_file(zf, src, f"{prefix}/{rel}")

    print(f"Wrote: {out_path} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
