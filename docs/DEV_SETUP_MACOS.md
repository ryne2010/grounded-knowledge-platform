# macOS development setup (Apple Silicon)

This repo is designed to be developed on an Apple Silicon Mac (e.g. an M2 Max MacBook Pro) and deployed to **Cloud Run**.

## Prereqs

- **Homebrew**
- **Python 3.11+**
- **uv** (Python packaging + runners)
- **Node.js 20+**
- **pnpm** (via Corepack)
- **Google Cloud SDK** (`gcloud`)
- **Terraform** (only if you plan to modify infra)

Optional:

- **tesseract** (only needed if you want OCR for scanned PDFs)

### Suggested installs

```bash
brew install python@3.11
brew install uv
brew install node
brew install --cask google-cloud-sdk

# pnpm via Corepack (recommended)
corepack enable
corepack prepare pnpm@9.15.0 --activate

# Optional OCR dependency (scanned PDFs)
brew install tesseract
```

If you plan on changing infrastructure:

```bash
brew install terraform
```

## Local setup

```bash
uv sync --dev
cd web && corepack pnpm install
```

Create a `.env`:

```bash
cp .env.example .env
```

For **full local development** (uploads, eval, chunk view), set these in `.env`:

```bash
PUBLIC_DEMO_MODE=0
ALLOW_UPLOADS=1
ALLOW_EVAL=1
ALLOW_CHUNK_VIEW=1

# Grounding: refuse answers without citations (recommended)
CITATIONS_REQUIRED=1

# Optional: enable deletes locally
ALLOW_DOC_DELETE=1

# Optional: keep demo docs even in private mode
BOOTSTRAP_DEMO_CORPUS=1

# Optional: OCR for scanned PDFs (requires `tesseract`)
OCR_ENABLED=1
```

## Run locally

API (FastAPI):

```bash
make run-api
```

UI (Vite dev server):

```bash
make run-ui
```

Or run both concurrently:

```bash
make dev
```

Quality gates / maintenance:

```bash
make test
make eval
make safety-eval
make purge-expired
```

Open:

- UI: `http://localhost:5173`
- API docs: `http://localhost:8080/api/swagger`

## Notes for Apple Silicon

- Cloud Run runs Linux containers; production images should be built for `linux/amd64`.
- This repo’s deploy workflow uses **Cloud Build** to avoid cross-arch Docker issues on Apple Silicon.

If you need to build locally for testing, use `docker buildx` and specify a platform:

```bash
docker buildx build --platform linux/amd64 -f docker/Dockerfile -t gkp:local .
```
