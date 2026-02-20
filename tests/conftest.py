"""pytest configuration.

This repo is intentionally usable without installing the package into a virtualenv.

When running `pytest` directly from the repo root, we want `import app` to resolve to
`./app`. Some environments / runners do not automatically add the repo root to
`sys.path` (notably certain CI wrappers and tracing/instrumentation layers), so we
force it here.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
