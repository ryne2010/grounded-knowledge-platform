#!/usr/bin/env bash
set -euo pipefail

# Local developer preflight + quality harness.
#
# This script is intentionally safe to run on a laptop (no cloud calls).

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd python
need_cmd uv
need_cmd node
need_cmd pnpm

python -c "import sys; assert sys.version_info >= (3,11), sys.version" >/dev/null
node -e "const [maj]=process.versions.node.split('.'); if (Number(maj) < 20) process.exit(1);" || {
  echo "Node 20+ required" >&2
  exit 1
}

# Use uv-managed environment when available.
PY_RUNNER="python"
if command -v uv >/dev/null 2>&1 && [ -f uv.lock ]; then
  PY_RUNNER="uv run python"
fi

echo "==> Lint"
$PY_RUNNER scripts/harness.py lint

echo "==> Typecheck"
$PY_RUNNER scripts/harness.py typecheck

echo "==> Tests"
$PY_RUNNER scripts/harness.py test

echo "==> Build web"
$PY_RUNNER scripts/harness.py build

echo "All checks passed." 
