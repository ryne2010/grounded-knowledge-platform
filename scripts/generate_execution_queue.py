#!/usr/bin/env python3
"""Generate docs/BACKLOG/QUEUE.md from docs/BACKLOG/MILESTONES.md.

Why:
- `docs/BACKLOG/MILESTONES.md` is the source of truth for *sequencing*, but it's prose.
- `docs/BACKLOG/QUEUE.md` is an execution-oriented view (ordered steps, quick links, sub-agent hints).

Usage:
  python scripts/generate_execution_queue.py

The output file is overwritten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MILESTONES_PATH = ROOT / "docs" / "BACKLOG" / "MILESTONES.md"
TASKS_DIR = ROOT / "agents" / "tasks"
OUT_PATH = ROOT / "docs" / "BACKLOG" / "QUEUE.md"


_TASK_REF_RE = re.compile(r"`(agents/tasks/[^`]+\.md)`")


@dataclass
class TaskInfo:
    filename: str
    title: str
    owner: str
    spec: str
    subagent: str


@dataclass
class Milestone:
    key: str
    title: str
    tasks: list[str]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
            # Prefer backtick path if present.
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
            # fallback: anything after ':'
            if ":" in line:
                return line.split(":", 1)[1].strip()
    return ""


def _load_task_info(filename: str) -> TaskInfo:
    p = TASKS_DIR / filename
    md = _read_text(p)
    return TaskInfo(
        filename=filename,
        title=_extract_title(md),
        owner=_extract_owner(md),
        spec=_extract_spec(md),
        subagent=_extract_subagent(md),
    )


def _parse_milestones(md: str) -> list[Milestone]:
    """Parse milestones and their primary task lists."""

    milestones: list[Milestone] = []
    current: Milestone | None = None
    in_primary_tasks = False

    def _start_milestone(heading: str) -> None:
        nonlocal current, in_primary_tasks
        key = heading.split()[0].strip()
        current = Milestone(key=key, title=heading.strip(), tasks=[])
        milestones.append(current)
        # Optional milestones (MO*) list tasks directly under the heading.
        in_primary_tasks = key.startswith("MO")

    for raw in md.splitlines():
        line = raw.rstrip("\n")

        if line.startswith("## "):
            _start_milestone(line.removeprefix("## ").strip())
            continue

        if line.startswith("### "):
            # Optional milestones live under the "Optional milestones" section.
            heading = line.removeprefix("### ").strip()
            if heading.startswith("MO"):
                _start_milestone(heading)
            continue

        if not current:
            continue

        if line.strip().lower().startswith("**primary tasks**"):
            in_primary_tasks = True
            continue

        # Stop capturing when we hit exit criteria.
        if line.strip().lower().startswith("**exit criteria**"):
            in_primary_tasks = False
            continue

        if not in_primary_tasks:
            continue

        m = _TASK_REF_RE.search(line)
        if not m:
            continue

        task_path = m.group(1)
        filename = task_path.split("/")[-1]
        if filename not in current.tasks:
            current.tasks.append(filename)

    # Only milestones that actually have tasks.
    return [m for m in milestones if m.tasks]


def main() -> int:
    md = _read_text(MILESTONES_PATH)
    milestones = _parse_milestones(md)

    lines: list[str] = []
    lines.append("# Execution queue")
    lines.append("")
    lines.append("This is the canonical, ordered execution queue derived from `docs/BACKLOG/MILESTONES.md`.")
    lines.append("")
    lines.append("Regenerate:")
    lines.append("")
    lines.append("```bash")
    lines.append("make queue")
    lines.append("```")
    lines.append("")
    lines.append("Guardrails:")
    lines.append("- Non-negotiables: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`")
    lines.append("- Execution playbook: `docs/BACKLOG/CODEX_PLAYBOOK.md`")

    step = 1
    for ms in milestones:
        lines.append("")
        lines.append(f"## {ms.title}")
        lines.append("")
        lines.append("| # | Task | Owner | Suggested sub-agent | Prompt pack |")
        lines.append("|---:|---|---|---|---|")

        for fname in ms.tasks:
            info = _load_task_info(fname)
            task_rel = f"../../agents/tasks/{fname}"
            spec_cell = ""
            if info.spec:
                # Normalize spec path to a repo-relative link.
                spec_path = info.spec
                spec_rel = "../../" + spec_path.replace("./", "")
                spec_cell = f"<br/>Spec: [`{spec_path}`]({spec_rel})"

            subagent_cell = f"`{info.subagent}`" if info.subagent else ""
            prompt_cmd = f"`make codex-prompt TASK=agents/tasks/{fname}`"

            lines.append(
                "| "
                + str(step)
                + " | "
                + f"[`{fname}`]({task_rel})<br/>{info.title}{spec_cell}"
                + " | "
                + (info.owner or "")
                + " | "
                + subagent_cell
                + " | "
                + prompt_cmd
                + " |"
            )
            step += 1



    # Unsequenced tasks (exist as TASK_*.md but not referenced in MILESTONES.md)
    sequenced = {t for ms in milestones for t in ms.tasks}
    all_task_files = sorted(
        [p.name for p in TASKS_DIR.glob("TASK_*.md") if p.is_file() and p.name != "TASK_TEMPLATE.md"]
    )
    unsequenced = [f for f in all_task_files if f not in sequenced]

    if unsequenced:
        lines.append("")
        lines.append("## Unsequenced tasks")
        lines.append("")
        lines.append(
            "These task files exist but are not currently referenced in `docs/BACKLOG/MILESTONES.md` "
            "(so they are not in the numbered queue above)."
        )
        lines.append("")
        lines.append("| Task | Owner | Suggested sub-agent |")
        lines.append("|---|---|---|")
        for fname in unsequenced:
            info = _load_task_info(fname)
            task_rel = f"../../agents/tasks/{fname}"
            subagent_cell = f"`{info.subagent}`" if info.subagent else ""
            lines.append(f"| [`{fname}`]({task_rel})<br/>{info.title} | {info.owner} | {subagent_cell} |")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({step-1} steps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
