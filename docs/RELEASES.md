# Releases

This document defines the repository release process and version/changelog discipline.

## Version strategy

This repo uses semantic versioning (`MAJOR.MINOR.PATCH`) as the release identifier.

Source of truth:
- `pyproject.toml` `[project].version`

Runtime behavior:
- `app/version.py` should not be manually edited for each release.
- `app/version.py` resolves the app version from installed package metadata first, then falls back to `pyproject.toml`.
- `APP_VERSION` remains an override knob for runtime environments when needed.

## Changelog strategy

`CHANGELOG.md` follows Keep a Changelog style:
- all incoming changes go under `## Unreleased`
- each cut release gets a dated section: `## X.Y.Z - YYYY-MM-DD`
- sections use consistent buckets (`Added`, `Changed`, `Fixed`)

## Release commands

Prereqs:
- clean working tree
- all CI/harness checks green

### 1) Prepare release content

Make sure `CHANGELOG.md` has accurate entries under `## Unreleased`.

### 2) Bump version and roll changelog

```bash
make release-bump VERSION=0.11.0
```

Optional explicit release date:

```bash
make release-bump VERSION=0.11.0 RELEASE_DATE=2026-02-22
```

What this does:
- updates `pyproject.toml` version
- creates `## 0.11.0 - YYYY-MM-DD` in `CHANGELOG.md` from the current `Unreleased` content
- resets `## Unreleased` to a standard template

### 3) Validate before tagging

```bash
make dev-doctor
python scripts/harness.py lint
python scripts/harness.py typecheck
python scripts/harness.py test
```

### 4) Generate release notes artifact

```bash
make release-notes VERSION=0.11.0
```

Default output:
- `dist/release_notes_0.11.0.md`

Custom output:

```bash
make release-notes VERSION=0.11.0 RELEASE_NOTES_OUT=dist/notes-v0.11.0.md
```

### 5) Tag and publish

```bash
git commit -m "release: 0.11.0"
git tag v0.11.0
git push origin main --tags
```

Use the generated notes file as the GitHub release body.

## Contributor checklist

1. Add change entries to `CHANGELOG.md` under `Unreleased` in the same PR as the change.
2. Keep entries concise and user-visible (avoid internal refactor noise unless behavior changed).
3. Do not edit old release sections retroactively except for factual corrections.
