#!/usr/bin/env bash
set -euo pipefail

uv sync --dev
uv run uvicorn app.main:app --reload --port 8080
