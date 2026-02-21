#!/usr/bin/env python3
"""Generate docs/BACKLOG/TASK_INDEX.md from agents/tasks/.

Why:
- Keeping the task index in sync manually is error-prone.
- This script produces a stable, sorted table.
- It enriches rows with milestone + suggested sub-agent + spec link for faster routing.

Usage:
  python scripts/generate_task_index.py

The output file is overwritten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "agents" / "tasks"
OUT_PATH = ROOT / "docs" / "BACKLOG" / "TASK_INDEX.md"
MILESTONES_PATH = ROOT / "docs" / "BACKLOG" / "MILESTONES.md"

_TASK_REF_RE = re.compile(r"`(agents/tasks/[^`]+\.md)`")


@dataclass(frozen=True)
class TaskMeta:
    filename: str
    title: str
    milestone: str
    owner: str
    subagent: str
    spec: str


def _extract_title(md: str) -> str:
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return "(missing title)"


def _extract_owner(md: str) -> str:
    for line in md.splitlines():
        # Only parse task "front matter" (avoid YAML examples, etc.).
        if line.strip().startswith("## "):
            break
        if line.lower().startswith("owner:"):
            return line.split(":", 1)[1].strip()
    return ""


def _extract_spec(md: str) -> str:
    for line in md.splitlines():
        if line.strip().startswith("## "):
            break
        if line.lower().startswith("spec:"):
            m = re.search(r"`([^`]+)`", line)
            if m:
                return m.group(1).strip()
            return line.split(":", 1)[1].strip()
    return ""


def _extract_subagent(md: str) -> str:
    for line in md.splitlines():
        if line.strip().startswith("## "):
            break
        if "suggested sub-agent" in line.lower():
            m = re.search(r"`([^`]+)`", line)
            if m:
                return m.group(1).strip()
            if ":" in line:
                return line.split(":", 1)[1].strip()
    return ""


def _parse_milestones(md: str) -> tuple[dict[str, str], list[str]]:
    """Return ({task_filename: milestone_key}, milestone_order)."""

    mapping: dict[str, str] = {}
    order: list[str] = []

    current_key = ""
    in_primary = False

    def _set_milestone(heading: str) -> None:
        nonlocal current_key, in_primary
        current_key = heading.split()[0].strip()
        if current_key and current_key not in order:
            order.append(current_key)
        in_primary = current_key.startswith("MO")

    for raw in md.splitlines():
        line = raw.rstrip("\n")

        if line.startswith("## "):
            _set_milestone(line.removeprefix("## ").strip())
            continue
        if line.startswith("### "):
            heading = line.removeprefix("### ").strip()
            if heading.startswith("MO"):
                _set_milestone(heading)
            continue

        if line.strip().lower().startswith("**primary tasks**"):
            in_primary = True
            continue
        if line.strip().lower().startswith("**exit criteria**"):
            in_primary = False
            continue
        if not in_primary:
            continue

        m = _TASK_REF_RE.search(line)
        if not m:
            continue

        filename = m.group(1).split("/")[-1]
        if filename not in mapping:
            mapping[filename] = current_key

    return mapping, order


def main() -> int:
    milestone_map, milestone_order = _parse_milestones(MILESTONES_PATH.read_text(encoding="utf-8"))
    milestone_rank = {k: i for i, k in enumerate(milestone_order)}

    files = [p for p in TASKS_DIR.glob("*.md") if p.is_file()]

    metas: list[TaskMeta] = []
    for p in files:
        md = p.read_text(encoding="utf-8")
        metas.append(
            TaskMeta(
                filename=p.name,
                title=_extract_title(md),
                milestone=milestone_map.get(p.name, ""),
                owner=_extract_owner(md),
                subagent=_extract_subagent(md),
                spec=_extract_spec(md),
            )
        )

    def _sort_key(m: TaskMeta) -> tuple[int, str]:
        r = milestone_rank.get(m.milestone, 999)
        return (r, m.filename)

    metas.sort(key=_sort_key)

    lines: list[str] = []
    lines.append("# Task index")
    lines.append("")
    lines.append("This is a flat index of all task files under `agents/tasks/`.")
    lines.append("")
    lines.append("Regenerate:")
    lines.append("")
    lines.append("```bash")
    lines.append("make task-index")
    lines.append("```")
    lines.append("")
    lines.append("| Task | Milestone | Owner | Suggested sub-agent | Spec |")
    lines.append("|---|---|---|---|---|")

    for m in metas:
        rel = f"../../agents/tasks/{m.filename}"
        subagent = f"`{m.subagent}`" if m.subagent else ""

        spec_cell = ""
        if m.spec:
            spec_rel = "../../" + m.spec.lstrip("./")
            spec_cell = f"[`{m.spec}`]({spec_rel})"

        lines.append(
            f"| [`{m.filename}`]({rel})<br/>{m.title} | {m.milestone} | {m.owner} | {subagent} | {spec_cell} |"
        )

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(metas)} tasks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
