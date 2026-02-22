from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_tools.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_release_bump_updates_pyproject_and_rolls_changelog(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    changelog = tmp_path / "CHANGELOG.md"

    pyproject.write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    changelog.write_text(
        """# Changelog

## Unreleased

### Added

- Added release process docs.

### Fixed

- Fixed release smoke script typo.

## 0.1.0

### Added

- Initial release.
""",
        encoding="utf-8",
    )

    res = _run(
        "bump",
        "--version",
        "0.2.0",
        "--date",
        "2026-02-22",
        "--pyproject",
        str(pyproject),
        "--changelog",
        str(changelog),
    )
    assert res.returncode == 0, res.stderr

    pyproject_out = pyproject.read_text(encoding="utf-8")
    changelog_out = changelog.read_text(encoding="utf-8")

    assert 'version = "0.2.0"' in pyproject_out
    assert "## 0.2.0 - 2026-02-22" in changelog_out
    assert "- Added release process docs." in changelog_out
    assert "- Fixed release smoke script typo." in changelog_out
    assert "## Unreleased" in changelog_out
    assert "- _TBD_" in changelog_out


def test_release_notes_extracts_target_version(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    out = tmp_path / "release_notes.md"

    changelog.write_text(
        """# Changelog

## Unreleased

### Added

- _TBD_

## 1.2.3 - 2026-02-22

### Added

- Added release notes command.
""",
        encoding="utf-8",
    )

    res = _run("notes", "--version", "1.2.3", "--changelog", str(changelog), "--output", str(out))
    assert res.returncode == 0, res.stderr

    notes = out.read_text(encoding="utf-8")
    assert notes.startswith("## 1.2.3 - 2026-02-22")
    assert "- Added release notes command." in notes


def test_release_notes_fails_for_missing_version(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## Unreleased\n\n### Added\n\n- _TBD_\n", encoding="utf-8")

    res = _run("notes", "--version", "9.9.9", "--changelog", str(changelog))
    assert res.returncode == 2
    assert "Version 9.9.9 not found" in res.stderr
