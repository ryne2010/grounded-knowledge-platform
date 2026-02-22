#!/usr/bin/env python3
"""Release workflow helpers.

Commands:
- bump: update pyproject version and roll CHANGELOG "Unreleased" into a dated release entry.
- notes: extract release notes for a version from CHANGELOG.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
PYPROJECT_VERSION_RE = re.compile(r'(?m)^version\s*=\s*"[^"]+"\s*$')
UNRELEASED_RE = re.compile(r"(?ms)^## Unreleased\s*\n(?P<body>.*?)(?=^##\s+|\Z)")

UNRELEASED_TEMPLATE = """### Added

- _TBD_

### Changed

- _TBD_

### Fixed

- _TBD_
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _validate_semver(value: str) -> str:
    v = value.strip()
    if not SEMVER_RE.fullmatch(v):
        raise ValueError(f"Invalid version '{value}'. Expected semantic version X.Y.Z.")
    return v


def _parse_release_date(value: str | None) -> dt.date:
    if value is None:
        return dt.date.today()
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def _replace_project_version(pyproject_text: str, version: str) -> str:
    if not PYPROJECT_VERSION_RE.search(pyproject_text):
        raise ValueError("Could not find project version line in pyproject.toml.")
    return PYPROJECT_VERSION_RE.sub(f'version = "{version}"', pyproject_text, count=1)


def _release_block_match(changelog_text: str, version: str) -> re.Match[str] | None:
    pattern = re.compile(
        rf"(?ms)^(?P<header>##\s+{re.escape(version)}(?:\s*-\s*[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})?)\s*\n"
        rf"(?P<body>.*?)(?=^##\s+|\Z)"
    )
    return pattern.search(changelog_text)


def _roll_unreleased(changelog_text: str, version: str, release_date: dt.date) -> str:
    if _release_block_match(changelog_text, version):
        raise ValueError(f"CHANGELOG already contains a section for version {version}.")

    m = UNRELEASED_RE.search(changelog_text)
    if m is None:
        raise ValueError("CHANGELOG missing required '## Unreleased' section.")

    unreleased_body = m.group("body").strip()
    if not unreleased_body:
        unreleased_body = "### Changed\n\n- _No notable changes._"

    before = changelog_text[: m.start()]
    after = changelog_text[m.end() :].lstrip("\n")

    new_unreleased = f"## Unreleased\n\n{UNRELEASED_TEMPLATE.strip()}\n\n"
    release_header = f"## {version} - {release_date.isoformat()}"
    release_block = f"{release_header}\n\n{unreleased_body}\n\n"

    return f"{before}{new_unreleased}{release_block}{after}"


def cmd_bump(pyproject_path: Path, changelog_path: Path, version: str, release_date: dt.date) -> int:
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    changelog_text = changelog_path.read_text(encoding="utf-8")

    new_pyproject = _replace_project_version(pyproject_text, version)
    new_changelog = _roll_unreleased(changelog_text, version, release_date)

    pyproject_path.write_text(new_pyproject, encoding="utf-8")
    changelog_path.write_text(new_changelog, encoding="utf-8")

    print(f"Updated {pyproject_path} -> version {version}")
    print(f"Updated {changelog_path} -> added section {version} ({release_date.isoformat()})")
    return 0


def cmd_notes(changelog_path: Path, version: str, output_path: str) -> int:
    changelog_text = changelog_path.read_text(encoding="utf-8")
    m = _release_block_match(changelog_text, version)
    if m is None:
        raise ValueError(f"Version {version} not found in {changelog_path}.")

    header = m.group("header").strip()
    body = m.group("body").strip()
    notes = f"{header}\n\n{body}\n"

    if output_path == "-":
        sys.stdout.write(notes)
        return 0

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(notes, encoding="utf-8")
    print(f"Wrote release notes: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    root = _repo_root()
    default_pyproject = root / "pyproject.toml"
    default_changelog = root / "CHANGELOG.md"

    p = argparse.ArgumentParser(prog="release_tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_bump = sub.add_parser("bump", help="Bump pyproject version and roll CHANGELOG Unreleased.")
    p_bump.add_argument("--version", required=True, help="Release version (semantic version X.Y.Z).")
    p_bump.add_argument("--date", default=None, help="Release date (YYYY-MM-DD). Defaults to today.")
    p_bump.add_argument("--pyproject", default=str(default_pyproject), help="Path to pyproject.toml.")
    p_bump.add_argument("--changelog", default=str(default_changelog), help="Path to CHANGELOG.md.")

    p_notes = sub.add_parser("notes", help="Extract release notes for one version from CHANGELOG.")
    p_notes.add_argument("--version", required=True, help="Release version (semantic version X.Y.Z).")
    p_notes.add_argument("--changelog", default=str(default_changelog), help="Path to CHANGELOG.md.")
    p_notes.add_argument(
        "--output",
        default="-",
        help="Output file path. Use '-' to print to stdout. Default: '-'.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        version = _validate_semver(args.version)

        if args.cmd == "bump":
            release_date = _parse_release_date(args.date)
            return cmd_bump(
                pyproject_path=Path(args.pyproject),
                changelog_path=Path(args.changelog),
                version=version,
                release_date=release_date,
            )

        if args.cmd == "notes":
            return cmd_notes(changelog_path=Path(args.changelog), version=version, output_path=args.output)

        raise ValueError(f"Unknown command: {args.cmd}")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
