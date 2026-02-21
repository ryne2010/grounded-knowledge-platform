#!/usr/bin/env python3
"""Prepare a single, copy/paste-friendly prompt pack for a task.

Why:
- When using a coding agent (@codex), it's easy to lose repo context.
- This script composes the task + referenced specs + non-negotiables into one markdown file.

Usage:
  python scripts/prepare_codex_prompt.py agents/tasks/TASK_UI_UX_POLISH.md

Outputs:
  dist/codex_prompts/<TASK_FILE>.prompt.md

Notes:
- The prompt pack intentionally includes only *critical* context (task/spec/ADR) to stay readable.
- It links to other repo docs instead of embedding everything.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = ROOT / "docs" / "DECISIONS" / "ADR-20260221-public-demo-and-deployment-model.md"
CODEX_PLAYBOOK = ROOT / "docs" / "BACKLOG" / "CODEX_PLAYBOOK.md"

_SPEC_LINE_RE = re.compile(r"^\s*spec\s*:\s*(.*)$", re.IGNORECASE)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_spec_paths(task_md: str) -> list[str]:
    paths: list[str] = []
    for line in task_md.splitlines():
        m = _SPEC_LINE_RE.match(line.strip())
        if not m:
            continue
        rest = m.group(1)
        # Prefer backtick content.
        bt = re.findall(r"`([^`]+)`", rest)
        if bt:
            for p in bt:
                if p not in paths:
                    paths.append(p)
        else:
            p = rest.strip()
            if p and p not in paths:
                paths.append(p)
    return paths


def _normalize_repo_path(p: str) -> Path:
    # Allow inputs like "docs/SPECS/foo.md" or "./docs/SPECS/foo.md".
    p = p.strip().lstrip("./")
    return ROOT / p


def main() -> int:
    ap = argparse.ArgumentParser(prog="prepare_codex_prompt")
    ap.add_argument("task", help="Path to a task markdown file, e.g. agents/tasks/TASK_*.md")
    ap.add_argument("--out", default="", help="Optional output path (defaults to dist/codex_prompts/<task>.prompt.md)")
    args = ap.parse_args()

    task_path = _normalize_repo_path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task not found: {task_path}")

    task_md = _read_text(task_path)
    spec_paths = _extract_spec_paths(task_md)

    out_path: Path
    if args.out:
        out_path = Path(args.out).expanduser().resolve()
    else:
        out_dir = ROOT / "dist" / "codex_prompts"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{task_path.name}.prompt.md"

    parts: list[str] = []
    parts.append(f"# Codex Prompt Pack — {task_path.name}")
    parts.append("")
    parts.append("Use this file as the single source of context for implementing the task with a coding agent.")
    parts.append("")

    parts.append("## Quick links")
    parts.append("")
    parts.append("- Non-negotiables (ADR): `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`")
    parts.append("- Execution workflow: `docs/BACKLOG/CODEX_PLAYBOOK.md`")
    parts.append("- Repo agent guidance: `AGENTS.md`")
    parts.append("")

    parts.append("## Non-negotiables (must not violate)")
    parts.append("")
    parts.append(_read_text(ADR_PATH).strip())
    parts.append("")

    parts.append("## Task")
    parts.append("")
    parts.append(task_md.strip())
    parts.append("")

    if spec_paths:
        parts.append("## Referenced specs")
        parts.append("")
        for sp in spec_paths:
            p = _normalize_repo_path(sp)
            if p.exists():
                parts.append(f"### {sp}")
                parts.append("")
                parts.append(_read_text(p).strip())
                parts.append("")
            else:
                parts.append(f"- (missing) {sp}")
        parts.append("")

    parts.append("## Execution checklist")
    parts.append("")
    parts.append("Follow the repo playbook; keep diffs small and validate locally:")
    parts.append("")
    parts.append("```bash")
    parts.append("make dev-doctor")
    parts.append("python scripts/harness.py lint")
    parts.append("python scripts/harness.py test")
    parts.append("python scripts/harness.py typecheck")
    parts.append("```")
    parts.append("")
    parts.append("If this task changes a repo contract or invariant, write an ADR first.")
    parts.append("")

    # Include the playbook tail as a reminder (not the whole file).
    playbook = _read_text(CODEX_PLAYBOOK).strip().splitlines()
    tail = "\n".join(playbook[-35:]) if len(playbook) > 35 else "\n".join(playbook)
    parts.append("## Review checklist excerpt")
    parts.append("")
    parts.append(tail)
    parts.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
