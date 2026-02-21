#!/usr/bin/env python3
"""Backlog / planning audit.

This script is intentionally lightweight: it validates that planning artifacts and task
metadata are consistent and "codex-ready".

It does **not** regenerate TASK_INDEX/QUEUE (use `make backlog-refresh` for that).

Usage:
  python scripts/backlog_audit.py

Exit codes:
  0 - OK
  1 - errors found
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "agents" / "tasks"
MILESTONES_PATH = ROOT / "docs" / "BACKLOG" / "MILESTONES.md"

_TASK_REF_RE = re.compile(r"`(agents/tasks/[^`]+\.md)`")


REQUIRED_FILES = [
    ROOT / "AGENTS.md",
    ROOT / "docs" / "DECISIONS" / "ADR-20260221-public-demo-and-deployment-model.md",
    ROOT / "docs" / "PRODUCT" / "PRODUCT_BRIEF.md",
    ROOT / "docs" / "PRODUCT" / "FEATURE_MATRIX.md",
    ROOT / "docs" / "BACKLOG" / "README.md",
    ROOT / "docs" / "BACKLOG" / "EPICS.md",
    ROOT / "docs" / "BACKLOG" / "MILESTONES.md",
    ROOT / "docs" / "BACKLOG" / "DEPENDENCIES.md",
    ROOT / "docs" / "BACKLOG" / "TASK_INDEX.md",
    ROOT / "docs" / "BACKLOG" / "QUEUE.md",
    ROOT / "docs" / "BACKLOG" / "CODEX_PLAYBOOK.md",
]


@dataclass
class Finding:
    kind: str  # "ERROR" or "WARN"
    message: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _front_matter_lines(md: str) -> list[str]:
    """Return lines before the first '## ' heading.

    Task metadata (Spec/Owner/Suggested sub-agent) is expected to live here.
    """

    out: list[str] = []
    for line in md.splitlines():
        if line.strip().startswith("## "):
            break
        out.append(line.rstrip("\n"))
    return out


def _extract_owner(front: list[str]) -> str:
    for line in front:
        if line.strip().lower().startswith("owner:"):
            return line.split(":", 1)[1].strip()
    return ""


def _extract_spec(front: list[str]) -> str:
    for line in front:
        if line.strip().lower().startswith("spec:"):
            m = re.search(r"`([^`]+)`", line)
            if m:
                return m.group(1).strip()
            return line.split(":", 1)[1].strip()
    return ""


def _extract_subagent(front: list[str]) -> str:
    for line in front:
        if "suggested sub-agent" in line.lower():
            m = re.search(r"`([^`]+)`", line)
            if m:
                return m.group(1).strip()
            if ":" in line:
                return line.split(":", 1)[1].strip()
    return ""


def _has_heading(md: str, heading: str) -> bool:
    # Case-insensitive, matches e.g. "## Acceptance criteria"
    pat = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    return bool(pat.search(md))


def _path_exists(rel: str) -> bool:
    p = (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except Exception:
        return False
    return p.exists()


def audit() -> tuple[list[Finding], list[Finding]]:
    errors: list[Finding] = []
    warns: list[Finding] = []

    # Required planning artifacts
    for p in REQUIRED_FILES:
        if not p.exists():
            errors.append(Finding("ERROR", f"Missing required planning artifact: {p.relative_to(ROOT)}"))

    # Milestone references
    if MILESTONES_PATH.exists():
        md = _read_text(MILESTONES_PATH)
        refs = _TASK_REF_RE.findall(md)
        for ref in refs:
            if not _path_exists(ref):
                errors.append(Finding("ERROR", f"Milestones references missing task file: {ref}"))

    # Task audits
    task_files = sorted([p for p in TASKS_DIR.glob("TASK_*.md") if p.is_file() and p.name != "TASK_TEMPLATE.md"])

    for p in task_files:
        md = _read_text(p)
        front = _front_matter_lines(md)
        owner = _extract_owner(front)
        spec = _extract_spec(front)
        subagent = _extract_subagent(front)

        if not owner:
            errors.append(Finding("ERROR", f"{p.name}: missing front-matter Owner: ..."))

        if spec and not _path_exists(spec):
            errors.append(Finding("ERROR", f"{p.name}: Spec path not found: {spec}"))

        if subagent and not _path_exists(subagent):
            errors.append(Finding("ERROR", f"{p.name}: Suggested sub-agent path not found: {subagent}"))

        if not _has_heading(md, "Acceptance criteria"):
            warns.append(Finding("WARN", f"{p.name}: missing '## Acceptance criteria' section"))

        if not (_has_heading(md, "Validation") or _has_heading(md, "Tests")):
            warns.append(Finding("WARN", f"{p.name}: missing '## Validation' or '## Tests' section"))

    return errors, warns


def main() -> int:
    errors, warns = audit()

    print("Backlog audit")
    print("============")
    print(f"Repo root: {ROOT}")

    if warns:
        print("\nWarnings:")
        for w in warns:
            print(f"- {w.message}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"- {e.message}")
        print("\nFAIL")
        return 1

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
