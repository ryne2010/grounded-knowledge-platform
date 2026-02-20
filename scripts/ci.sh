#!/usr/bin/env bash
set -euo pipefail

# CI entrypoint.
# Assumes deps are installed (uv sync --dev, pnpm install).

PY_RUNNER="python"
if command -v uv >/dev/null 2>&1 && [ -f uv.lock ]; then
  PY_RUNNER="uv run python"

  # Ensure the lockfile is portable (no internal/private index URLs).
  if grep -q "applied-caas-gateway" uv.lock || grep -q "artifactory/api/pypi" uv.lock; then
    echo "ERROR: uv.lock contains non-portable index URLs. Regenerate with PyPI (https://pypi.org/simple)." >&2
    exit 1
  fi
fi

$PY_RUNNER scripts/harness.py lint
$PY_RUNNER scripts/harness.py typecheck
$PY_RUNNER scripts/harness.py test
$PY_RUNNER scripts/harness.py build
