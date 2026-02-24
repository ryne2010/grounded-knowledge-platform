### Build frontend (React + TanStack) ###
FROM node:20-alpine AS frontend

WORKDIR /app/web

# Use pnpm via corepack (preferred by this portfolio).
RUN corepack enable

COPY web/package.json web/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

COPY web/ ./
RUN pnpm build


### Build/runtime backend (FastAPI) ###
FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_DEFAULT_INDEX=https://pypi.org/simple \
    UV_HTTP_RETRIES=10 \
    UV_HTTP_TIMEOUT=120 \
    UV_HTTP_CONNECT_TIMEOUT=30 \
    UV_CONCURRENT_DOWNLOADS=4 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080

WORKDIR /app

# System deps
# - tesseract: optional OCR support (fully open source)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
 && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

# If you generate a lockfile locally (`uv lock`), feel free to copy it into the image
# to make builds more reproducible.
COPY uv.lock ./

# Install runtime deps + deployment extras:
# - cloudsql: psycopg for Postgres/Cloud SQL connectivity
# - observability: OpenTelemetry SDK/instrumentation
RUN set -euo pipefail; \
    if grep -Eq "packages\\.applied-caas-gateway1|pypi-public/simple" uv.lock; then \
      echo "uv.lock references mirror URLs; refreshing lock against ${UV_DEFAULT_INDEX}"; \
      uv lock --refresh --no-progress; \
    fi; \
    max_attempts=5; \
    for attempt in $(seq 1 "${max_attempts}"); do \
      echo "uv sync attempt ${attempt}/${max_attempts}"; \
      if uv sync --no-dev --no-install-project --extra cloudsql --extra observability --frozen --no-progress; then \
        exit 0; \
      fi; \
      if [ "${attempt}" -eq "${max_attempts}" ]; then \
        break; \
      fi; \
      sleep_seconds=$((attempt * 10)); \
      echo "Retrying in ${sleep_seconds}s..."; \
      sleep "${sleep_seconds}"; \
    done; \
    echo "uv sync failed after ${max_attempts} attempts"; \
    exit 1

COPY app ./app
COPY data ./data
COPY docs ./docs
COPY infra ./infra
COPY scripts ./scripts

# Copy built web assets
COPY --from=frontend /app/web/dist ./web/dist

# Harden: run as non-root.
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app \
    && chmod -R a+rX /opt/venv
USER app

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
