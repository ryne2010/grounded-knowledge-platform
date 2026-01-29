### Build frontend (React + TanStack) ###
FROM node:20-alpine AS frontend

WORKDIR /app/web

# Use pnpm via corepack (preferred by this portfolio).
RUN corepack enable

COPY web/package.json web/pnpm-lock.yaml* ./
RUN pnpm install --no-frozen-lockfile

COPY web/ ./
RUN pnpm build


### Build/runtime backend (FastAPI) ###
FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080

WORKDIR /app

# System deps
# - build-essential: some Python wheels may require compilation
# - tesseract: optional OCR support (fully open source)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
 && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

# If you generate a lockfile locally (`uv lock`), feel free to copy it into the image
# to make builds more reproducible.
# COPY uv.lock ./

# Install only runtime deps into /opt/venv
RUN uv sync --no-dev --no-install-project

COPY app ./app
COPY data ./data
COPY docs ./docs
COPY infra ./infra
COPY scripts ./scripts

# Copy built web assets
COPY --from=frontend /app/web/dist ./web/dist

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
