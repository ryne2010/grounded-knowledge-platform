from __future__ import annotations

from pathlib import Path


def get_version() -> str:
    """Best-effort version resolution.

    Order:
      1) Installed package metadata (when installed as a package)
      2) pyproject.toml (repo / container build context)
      3) fallback
    """

    # 1) installed metadata
    try:
        from importlib.metadata import version as _version  # py3.8+

        return _version("grounded-knowledge-platform")
    except Exception:
        pass

    # 2) pyproject.toml
    try:
        import tomllib  # py3.11+

        root = Path(__file__).resolve().parents[1]
        pyproject = root / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        v = data.get("project", {}).get("version")
        if isinstance(v, str) and v.strip():
            return v.strip()
    except Exception:
        pass

    return "0.0.0"
