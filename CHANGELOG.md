# Changelog

All notable changes to this repository will be documented here.

The project follows (roughly) [Keep a Changelog](https://keepachangelog.com/) and semantic versioning.

## 0.10.0

### Fixed

- Fixed a runtime `NameError` in the readiness probe logging path.
- Fixed a type-check edge case in retrieval eval metrics (MRR).
- Fixed SQLite FTS5 index maintenance to avoid duplicate rows by relying on triggers.

### Added

- `make clean` and `make dist` targets:
  - `make clean` removes local caches/build artifacts.
  - `make dist` creates a clean source ZIP that excludes build artifacts and secrets.
- `scripts/package_repo.py` and `scripts/clean.sh` to support the targets above.
- Docs UI: added retention + status columns (expired/active/kept).

### Changed

- Web install now uses `pnpm install --frozen-lockfile` for reproducible builds.

## 0.9.0

- Prior hardened release.
