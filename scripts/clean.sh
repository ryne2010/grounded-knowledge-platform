#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf \
  .pytest_cache \
  .ruff_cache \
  .mypy_cache \
  .coverage \
  htmlcov \
  dist \
  web/dist \
  .cache \
  .hypothesis \
  .pytest_cache \
  .uv \
  build \
  *.egg-info || true

# Remove Python bytecode caches (but don't crawl into virtualenvs or node_modules).
find . \
  -type d \( -name .venv -o -name node_modules \) -prune -false \
  -o -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf

find . \
  -type d \( -name .venv -o -name node_modules \) -prune -false \
  -o -type f -name '*.pyc' -print0 | xargs -0 -r rm -f

echo "Cleaned repo artifacts."
