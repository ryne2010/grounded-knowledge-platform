# Manual deploy to GCP (Cloud Run + Terraform + Cloud Build)

This guide deploys the **Grounded Knowledge Platform** as a single **public Cloud Run** service using:

- **Terraform** (in `infra/gcp/cloud_run_demo/`)
- **Remote Terraform state** in **GCS** (versioned)
- **Cloud Build** to build/push the container image (macOS Apple Silicon friendly)
- **Safe demo defaults** (`PUBLIC_DEMO_MODE=1`, extractive-only, rate limiting)

> This intentionally mirrors common “Cloud Engineer” responsibilities: repeatable IaC, CI-friendly builds, IAM, and safe operations.

Optional CI/CD (WIF):

- If you want GitHub Actions → GCP auth without keys, see `docs/WIF_GITHUB_ACTIONS.md`.
- This manual flow uses the same “Terraform config in GCS, downloaded at runtime” pattern as the CI workflows.

---

## Cost + safety guardrails (read first)

This repo is already configured for a “public demo that shouldn’t surprise you”:

- Cloud Run: `min_instances = 0`, `max_instances = 1` (scale-to-zero + hard cap)
- No Serverless VPC connector by default (connectors are **not free**)
- Demo mode disables uploads/eval and avoids external LLM calls

Still recommended (outside Terraform):

- Create a **Billing budget + alerts** (Budgets do not stop spending, but they warn you)
- Use an **immutable image tag** (avoid `latest` for rollback/debugging)

### Billing budget alert (Web UI)

Quick steps:

1. Cloud Console → **Billing**
2. Select your Billing account
3. Left nav → **Budgets & alerts** → **Create budget**
4. Scope: choose the project you’re deploying (or keep “All projects”)
5. Amount: set something low (example: `$20`)
6. Alerts: add email alerts at `50%`, `90%`, and `100%`
7. Save

Teaching points:

- A budget **does not cap** or stop spend — it’s an **alerting** mechanism.
- Alerts can be delayed; treat them as “smoke alarms”, not circuit breakers.
- If you want a hard cap, use **Cloud Run max instances**, remove expensive features (demo mode), and avoid always-on resources.

---

## Prereqs

- `gcloud` (authenticated)
- `terraform` (>= 1.5)
- Optional: `jq` (nice output parsing)

Auth (interactive):

```bash
: "Browser-based auth for CLI commands."
gcloud auth login

: "Application Default Credentials (ADC) for Terraform provider auth (no JSON keys)."
gcloud auth application-default login
```

Tip (common gotcha):

```bash
: "Avoid 'quota project' warnings and ensure API calls bill the right project."
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

---

## 1) One-time setup (avoid `export ...` via config files)

If you want to avoid repeating variables in your shell (and keep a “single source of truth”), use:

- **gcloud config** for `project` + `run/region`
- Terraform **backend config** (`backend.hcl`) for remote state location
- Terraform **vars** (`terraform.tfvars`) for stack inputs

This keeps your deploy commands short and reduces copy/paste errors.

> Teaching point: don’t confuse **Terraform state** (GCS backend) with **configuration**. State is *what exists*; config is *what you want*.

### 1a) Set gcloud defaults (one-time per machine/config)

This sets your local “context store” so commands don’t need repeated flags:

```bash
gcloud config set project "YOUR_PROJECT_ID"
gcloud config set run/region "us-central1"
: "Pick the region you want to run in."
```

Gotcha:

- If you use multiple projects, consider a dedicated config:
  `gcloud config configurations create personal-portfolio && gcloud config configurations activate personal-portfolio`
- You may see a warning like: `Project '...' lacks an 'environment' tag.`
  - That’s about **Resource Manager Tags** (org-level governance). In a personal project (no org/tag keys), you can ignore it.
  - Teaching point: **labels** are per-resource metadata; **tags** are org-managed and can drive policy/IAM at scale.

### 1b) Create a config bucket in GCS (one-time)

If you want configuration to live in **one place** (recommended), store `backend.hcl` + `terraform.tfvars` in GCS:

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="$(gcloud config get-value run/region)"

CONFIG_BUCKET="${PROJECT_ID}-config"

gcloud storage buckets describe "gs://${CONFIG_BUCKET}" >/dev/null 2>&1 \
  && echo "config bucket exists: gs://${CONFIG_BUCKET}" \
  || gcloud storage buckets create "gs://${CONFIG_BUCKET}" \
    --location="${REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention

: "Versioning is strongly recommended so you can roll back config changes."
gcloud storage buckets update "gs://${CONFIG_BUCKET}" --versioning
```

Teaching point:

- This bucket is *configuration*, not Terraform state. Keeping them separate avoids confusion and makes IAM simpler.

### 1c) Create `backend.hcl` + `terraform.tfvars` in GCS (one-time per environment)

Pick an env and a config “folder” (prefix):

```bash
ENV="dev"
: "ENV can be dev|stage|prod."
TF_CONFIG_GCS_PATH="gs://$(gcloud config get-value project)-config/gkp/${ENV}"
```

Now upload **backend.hcl** directly to GCS (no local file needed):

```bash
: "Remote state bucket created in step 2 (by convention: <project>-tfstate)."
TFSTATE_BUCKET="$(gcloud config get-value project)-tfstate"

cat <<EOF | gcloud storage cp - "${TF_CONFIG_GCS_PATH}/backend.hcl"
bucket = "${TFSTATE_BUCKET}"
prefix = "gkp/${ENV}"
EOF
```

Teaching point:

- `prefix` is a simple “blast radius” control. Each env writes state to a different key prefix in the same bucket.

Now upload **terraform.tfvars** (again, no local file needed). First, here’s example content (you do **not** need to create a local file):

```hcl
project_id        = "YOUR_PROJECT_ID"
region            = "us-central1"
env               = "dev"
service_name      = "gkp-dev"
artifact_repo_name = "gkp"

# Use an immutable tag for interviews when you’re ready (e.g., v2026-02-03-1).
# For lowest-friction demos, "latest" is OK (but you must still trigger a new revision).
image_name = "gkp"
image_tag  = "latest"

# Optional: demonstrate group-based IAM without Workspace/Cloud Identity.
clients_observers_group_email              = "job-search-ryne@googlegroups.com"
enable_clients_observers_monitoring_viewer = true
```

Upload it:

```bash
cat <<EOF | gcloud storage cp - "${TF_CONFIG_GCS_PATH}/terraform.tfvars"
project_id         = "$(gcloud config get-value project)"
region             = "$(gcloud config get-value run/region)"
env                = "${ENV}"
service_name       = "gkp-${ENV}"
artifact_repo_name = "gkp"
image_name         = "gkp"
image_tag          = "latest"

# Optional: demonstrate group-based IAM without Workspace/Cloud Identity.
clients_observers_group_email              = "job-search-ryne@googlegroups.com"
enable_clients_observers_monitoring_viewer = true
EOF
```

Gotchas:

- `terraform.tfvars` is auto-loaded by Terraform when you run in that directory (no `-var ...` flags needed).
- These files are intentionally **not committed**; `.gitignore` ignores `*.tfvars` and `backend.hcl`.
  - Teaching point: **do commit** `.terraform.lock.hcl`. It contains provider versions + checksums (no secrets) and makes runs reproducible across machines/CI.

### 1d) Download config into `infra/gcp/cloud_run_demo/` (each time you run Terraform)

Terraform expects local files for `terraform init` (backend config) and for auto-loading vars.
Think of this as a **local cache** of your “real” config in GCS — download, run Terraform, and move on.

```bash
ENV="dev"
TF_CONFIG_GCS_PATH="gs://$(gcloud config get-value project)-config/gkp/${ENV}"

gcloud storage cp "${TF_CONFIG_GCS_PATH}/backend.hcl" infra/gcp/cloud_run_demo/backend.hcl
gcloud storage cp "${TF_CONFIG_GCS_PATH}/terraform.tfvars" infra/gcp/cloud_run_demo/terraform.tfvars
```

Gotcha:

- Downloading into the repo is OK: these files are ignored by git and treated as ephemeral.

---

## 2) Create the Terraform remote state bucket (GCS, versioned)

Terraform state is **production data**. Versioning gives you rollback safety.

```bash
: "We standardize the tfstate bucket name for this repo to: <project>-tfstate."
: "(Bucket names are global; if it's taken, pick another and update backend.hcl.)"
TFSTATE_BUCKET="$(gcloud config get-value project)-tfstate"

gcloud storage buckets describe "gs://${TFSTATE_BUCKET}" >/dev/null 2>&1 \
  && echo "tfstate bucket exists: gs://${TFSTATE_BUCKET}" \
  || gcloud storage buckets create "gs://${TFSTATE_BUCKET}" \
  --location="$(gcloud config get-value run/region)" \
  --uniform-bucket-level-access \
  --public-access-prevention

: "Enable object versioning (important)."
gcloud storage buckets update "gs://${TFSTATE_BUCKET}" --versioning
```

Tips:

- Bucket names are global; if `<project>-tfstate` is taken, add a suffix.
- You can add lifecycle rules later (e.g., delete older noncurrent versions after 30–90 days).

---

## 3) Terraform init (remote backend)

This tells Terraform where to store state **before** creating anything.

```bash
terraform -chdir="infra/gcp/cloud_run_demo" init -reconfigure \
  -backend-config="backend.hcl"
```

Gotcha:

- If you change `bucket` or `prefix`, re-run `terraform init -reconfigure`.

---

## 4) Create prerequisite infra (APIs + Artifact Registry + runtime service account)

We do this first so the Artifact Registry repo exists before Cloud Build tries to push.

> Teaching note: `-target` is generally discouraged for day-to-day work, but it’s a practical bootstrap technique when you need “just enough infra” to unblock the next step (image push).

```bash
terraform -chdir="infra/gcp/cloud_run_demo" apply -auto-approve \
  -target=module.core_services \
  -target=module.artifact_registry \
  -target=module.service_accounts
```

---

## 5) Cloud Build push permissions (usually automatic)

This repo’s Terraform stack now grants Cloud Build permission to push to Artifact Registry **at the repo level**
(`google_artifact_registry_repository_iam_member.cloud_build_writer`), so you can usually skip any manual IAM steps here.

If your Cloud Build push fails with `PERMISSION_DENIED`, run this one-time fix:

```bash
PROJECT_ID="$(gcloud config get-value project)"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"

: "Cloud Build runs as <PROJECT_NUMBER>@cloudbuild.gserviceaccount.com"
: "Grant it permission to push images (project-level, broader than repo-level)."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

Teaching points / gotchas:

- Project-level IAM is broader than repo-level IAM, but it's a pragmatic personal-demo fix.
- This is the most common reason a build “succeeds” but the push fails (build OK, push denied).

---

## 6) Local smoke test (Docker build + run)

This is a fast “does the container start and respond?” check before you spend time in Cloud Build.

Build the image locally:

```bash
: "`-f docker/Dockerfile` selects the repo’s multi-stage Dockerfile (frontend build + backend runtime)."
: "`-t gkp:local` tags the image locally so you can run it by name."
: "The final image includes the built frontend assets + the FastAPI app."
docker build -f docker/Dockerfile -t gkp:local .
```

Run it (safe defaults recommended):

```bash
: "`--rm` deletes the container when it exits (keeps your machine clean)."
: "`-p 8080:8080` publishes host port 8080 → container port 8080."
: "`-e PUBLIC_DEMO_MODE=1` enables the safe public-demo configuration."
docker run --rm -p 8080:8080 \
  -e PUBLIC_DEMO_MODE=1 \
  gkp:local
```

In another terminal, hit the health endpoints:

```bash
curl -fsS "http://localhost:8080/health" >/dev/null && echo "OK: /health"
curl -fsS "http://localhost:8080/api/meta"
```

Teaching points / gotchas:

- Local build is for **fast feedback**; Cloud Build is for **CI parity** + the **real deploy artifact**.
- If you see `Bind for 0.0.0.0:8080 failed: port is already allocated`, something else is already using host port `8080`.
  - Option A (recommended): pick a different host port, e.g. `-p 18080:8080`, then curl `http://localhost:18080/...`
  - Option B: stop the thing using `8080` (see below).
- On Apple Silicon (M1/M2/M3), local Docker builds are often `linux/arm64`. Cloud Run commonly runs `linux/amd64`.
  - That mismatch is why we still build with Cloud Build even if the local smoke test passes.
- If the container starts but `/health` fails, check logs in the running container output first.

Debug: find/stop whatever is using port 8080

```bash
: "1) See which host process is listening on 8080 (macOS)."
lsof -nP -iTCP:8080 -sTCP:LISTEN

: "2) If the listener is 'com.docker', that usually means SOME CONTAINER is publishing 8080."
: "   List running containers and look for a Ports column containing '8080->'."
docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Ports}}'

: "3) Stop the container that is publishing 8080 (replace with the ID/name you found above)."
docker stop <container_id_or_name>
```

Teaching point:

- On macOS, Docker Desktop may appear as the host listener (`com.docker`) because it’s proxying traffic to a container.
  - Don’t `kill` the macOS PID from `lsof` unless you’re intentionally restarting Docker Desktop.

---

## 7) Build + push the image (Cloud Build)

This repo uses `cloudbuild.yaml` at the repo root, which expects `_IMAGE` as a substitution.

```bash
: "Preferred: get the image URI from Terraform outputs."
: "NOTE: Terraform outputs live in STATE, so we do a refresh-only apply to ensure outputs are present/up-to-date."
TF_DIR="infra/gcp/cloud_run_demo"

: "Refresh-only apply: reads real GCP resources and updates Terraform STATE/outputs, without changing infrastructure."
: "This assumes you already ran: terraform init (step 3) and downloaded backend.hcl + terraform.tfvars (step 1d)."
terraform -chdir="${TF_DIR}" apply -refresh-only -auto-approve

: "Read the image URI from state outputs as a raw string (no quotes) for CLI-friendly use."
IMAGE="$(terraform -chdir="${TF_DIR}" output -raw image)"
test -n "${IMAGE}" || { echo "ERROR: terraform output 'image' is empty" >&2; exit 1; }

: "Submit the repo as a Cloud Build source bundle. cloudbuild.yaml will docker-build and push to Artifact Registry."
: "The _IMAGE substitution is required; it's used as the docker tag + the pushed image reference."
gcloud builds submit --config cloudbuild.yaml --substitutions "_IMAGE=${IMAGE}" .
```

Gotchas:

- If you used `-target` during bootstrap, outputs can be stale/missing until you run an apply (refresh-only is the safest way).
- If you edit `terraform.tfvars`, `terraform output` won’t change until you run `terraform apply` (or `terraform apply -refresh-only`).

Why Cloud Build (teaching point):

- Apple Silicon (M1/M2/M3) local Docker builds often produce `arm64` images; Cloud Run expects `linux/amd64` by default.
- Cloud Build provides a consistent build environment and matches CI.

---

## 8) Terraform apply (Cloud Run + observability + optional group IAM)

This creates/updates the Cloud Run service and (by default) observability resources (dashboards/alerts/log views/SLOs).

```bash
terraform -chdir="infra/gcp/cloud_run_demo" apply -auto-approve
```

Notes:

- If `CLIENTS_OBSERVERS_GROUP_EMAIL` is empty, Terraform will skip group bindings.
- Group/IAM propagation can take a few minutes.

---

## 9) Get the service URL + verify

```bash
: "Prefer reading the URL from Terraform state outputs."
URL="$(terraform -chdir=infra/gcp/cloud_run_demo output -raw service_url)"

: "If the output is empty/stale, ask Cloud Run for the live URL."
if test -z "${URL}"; then
  SERVICE_NAME="$(terraform -chdir=infra/gcp/cloud_run_demo output -raw service_name)"
  URL="$(gcloud run services describe "${SERVICE_NAME}" \
    --region "$(gcloud config get-value run/region)" \
    --format='value(status.url)')"
fi

echo "${URL}"

: "Health + metadata endpoints should be fast and safe."
curl -fsS "${URL}/health" >/dev/null && echo "OK: /health"
curl -fsS "${URL}/api/meta" | jq
```

What you should see in `/api/meta` (teaching point):

- `public_demo_mode: true`
- `uploads_enabled: false`
- `eval_enabled: false`
- `llm_provider: extractive`

---

## Common troubleshooting

### “Permission denied” pushing to Artifact Registry

- Re-run the IAM binding step for Cloud Build writer (step 5).

### Terraform can’t authenticate to GCP

- Confirm ADC:
  `gcloud auth application-default print-access-token >/dev/null && echo OK`

### Terraform apply fails with “no route to host” / “client connection lost” / “Failed to upload state”

Symptoms you might see:

- `dial tcp ...: connect: no route to host`
- `http2: client connection lost`
- `Failed to upload state to gs://...`

What’s happening (teaching point):

- Terraform is talking to multiple Google APIs (Cloud Resource Manager, IAM, GCS backend).
  If your network drops mid-apply, Terraform can create real resources but fail to persist state.

Recovery:

```bash
TF_DIR="infra/gcp/cloud_run_demo"

: "1) First, fix connectivity (VPN/Wi‑Fi). Then confirm gcloud can reach GCP APIs."
gcloud projects describe "$(gcloud config get-value project)" --format='value(projectNumber)' >/dev/null && echo "OK: gcloud connectivity"

: "2) Make sure the backend is configured and state is reachable."
terraform -chdir="${TF_DIR}" init -reconfigure -backend-config="backend.hcl"
terraform -chdir="${TF_DIR}" state list | head

: "3) Retry the same apply command. Terraform is designed to be idempotent."
: "(If you get 'already exists' errors, see the note below about imports.)"
```

If Terraform tells you it wrote `errored.tfstate`:

- Keep that file.
- After connectivity returns, push it to the remote backend:
  - `terraform -chdir="${TF_DIR}" state push errored.tfstate`

If the apply created resources but state didn’t save (import note):

- You may need to import “already exists” resources back into state (common ones are the Artifact Registry repo + runtime SA), then re-apply.

### Cloud Run deploy fails with a memory/CPU error

Example:
- `Invalid value specified for memory. Total memory < 512 Mi is not supported with cpu always allocated (unthrottled).`

Fix:
- Use at least `512Mi` memory for the Cloud Run service, or switch to “CPU only during request” mode.
  - This repo defaults to `512Mi` for the demo to keep deploys simple and reliable.

Teaching point:
- Cloud Run has **constraints** between CPU allocation mode and minimum memory. Treat these like instance-type constraints on VMs.

### Log Views sink IAM error (member is empty)

Example:
- `invalid value "" for member` while creating `roles/logging.bucketWriter`

Fix:
- This can happen when a Logging sink’s `writer_identity` is empty for log-bucket destinations.
- Easiest workaround (if you hit this while experimenting): temporarily disable log views:
  - set `enable_log_views = false` in `terraform.tfvars`, then re-apply.

### Cloud Run container fails to start/listen on `PORT=8080`

Symptom:
- `The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable...`

Debug:
- Open the revision logs (the error usually includes a Logs URL), or run:
  - `gcloud run services logs read "gkp-dev" --region "$(gcloud config get-value run/region)" --limit 200`

Common causes (teaching points):
- **Slow startup work** (model downloads, heavy indexing) can cause Cloud Run to time out before the app binds the port.
  - This demo is designed to avoid that by using `EMBEDDINGS_BACKEND=hash` + `LLM_PROVIDER=extractive`.
- To isolate startup issues fast, set `bootstrap_demo_corpus = false` in your `terraform.tfvars` (in GCS), re-download it, and re-apply.

### Terraform can’t replace/destroy Cloud Run (deletion protection)

Symptom:
- `cannot destroy service without setting deletion_protection=false and running terraform apply`

What it means (teaching point):
- The Cloud Run service has **deletion protection enabled**, so Terraform is not allowed to destroy it.
- This often happens right after a failed create, because Terraform marks the resource as **tainted** and tries to replace it.

Fast recovery (recommended):

```bash
TF_DIR="infra/gcp/cloud_run_demo"

: "1) Remove the taint so Terraform can do an in-place update instead of destroy+recreate."
terraform -chdir="${TF_DIR}" untaint module.cloud_run.google_cloud_run_v2_service.service

: "2) Re-apply. This will set deletion_protection=false (demo default in this repo) and create a fresh revision if needed."
terraform -chdir="${TF_DIR}" apply -auto-approve
```

If you need to find the exact resource address:

```bash
TF_DIR="infra/gcp/cloud_run_demo"
terraform -chdir="${TF_DIR}" state list | grep cloud_run_v2_service
```

### Cloud Run returns 500

- Read logs:
  `gcloud run services logs read "gkp-dev" --region "$(gcloud config get-value run/region)" --limit 100`

---

## Cleanup (avoid lingering costs)

Destroy Terraform-managed resources:

```bash
ENV="dev"
TF_DIR="infra/gcp/cloud_run_demo"
TF_CONFIG_GCS_PATH="gs://$(gcloud config get-value project)-config/gkp/${ENV}"

: "Refresh local cache of your GCS-hosted Terraform config."
gcloud storage cp "${TF_CONFIG_GCS_PATH}/backend.hcl" "${TF_DIR}/backend.hcl"
gcloud storage cp "${TF_CONFIG_GCS_PATH}/terraform.tfvars" "${TF_DIR}/terraform.tfvars"

: "Make sure Terraform is pointed at the remote GCS backend state."
terraform -chdir="${TF_DIR}" init -reconfigure -backend-config="backend.hcl"

: "Optional sanity check: preview what will be destroyed."
terraform -chdir="${TF_DIR}" plan -destroy

: "Destroy everything in this Terraform state."
terraform -chdir="${TF_DIR}" destroy -auto-approve
```

Notes:

- This does **not** delete the `tfstate` bucket (intentional). Delete it manually only when you’re done with the project.
- This does **not** delete the `config` bucket where you stored `backend.hcl` + `terraform.tfvars`. Delete it manually when you’re truly done.
- Artifact Registry images may remain; delete old tags if needed.
- If you also bootstrapped GitHub Actions WIF, that’s a separate Terraform root/state:
  - `terraform -chdir="infra/gcp/wif_bootstrap" destroy -auto-approve`
  - Teaching point: keep bootstrap state separate so “app deploy” and “CI identity” can evolve independently.

Redeploy note (after `destroy`):

- If you kept your `config` + `tfstate` buckets, you can redeploy by resuming from **Step 4** (bootstrap infra),
  then continue with **Steps 5 → 7 → 8 → 9**.
- Only repeat **Steps 1b/1c/2** if you deleted the buckets or changed your config prefix.

Destroy gotcha (Cloud Logging buckets):

- If `terraform destroy` fails with:
  - `Only buckets in state ACTIVE can be deleted`
- It usually means the service-scoped **Cloud Logging log bucket** is already in `DELETE_REQUESTED` (deletion is asynchronous).
  - Wait a minute or two and re-run destroy.
  - You can check status with:

```bash
PROJECT_ID="$(gcloud config get-value project)"
gcloud logging buckets describe "gkp-dev-logs" --project "${PROJECT_ID}" --location global --format='value(lifecycleState)'
```

Redeploy gotcha (Cloud Logging buckets):

- If `terraform apply` fails with:
  - `Buckets must be in an ACTIVE state to be modified`
- It usually means the log bucket is still in `DELETE_REQUESTED` from a prior destroy attempt.
  - Option A: wait (and retry) until the bucket is back to `ACTIVE`.
  - Option B (faster): **undelete** the bucket so it returns to `ACTIVE`, then re-apply:

```bash
PROJECT_ID="$(gcloud config get-value project)"
BUCKET_ID="gkp-dev-logs"

: "If this prints DELETE_REQUESTED, Terraform can't modify the bucket yet."
gcloud logging buckets describe "${BUCKET_ID}" --project "${PROJECT_ID}" --location global --format='value(lifecycleState)'

: "Bring it back to ACTIVE so Terraform can proceed."
gcloud logging buckets undelete "${BUCKET_ID}" --project "${PROJECT_ID}" --location global

: "Wait until the bucket reports ACTIVE (undelete is async)."
until test "$(gcloud logging buckets describe "${BUCKET_ID}" --project "${PROJECT_ID}" --location global --format='value(lifecycleState)')" = "ACTIVE"; do
  echo "waiting for ${BUCKET_ID} to become ACTIVE..."
  sleep 15
done

: "If a previous apply failed mid-create, Terraform may mark the bucket as TAINTED and try to replace it (destroy+create)."
: "Replacing a just-deleted log bucket is flaky because Cloud Logging uses a soft-delete lifecycle."
: "If you see 'is tainted, so must be replaced' for this resource, untaint it:"
: "zsh note: quote addresses with [0] so the shell doesn't treat them like globs."
terraform -chdir="infra/gcp/cloud_run_demo" untaint 'google_logging_project_bucket_config.service_logs[0]' || true

: "Re-run apply to finish converging the stack."
terraform -chdir="infra/gcp/cloud_run_demo" apply -auto-approve
```

Extra sanity check:

- If `terraform plan -destroy` only shows 1–2 resources (but you expect more), you may be pointing at the wrong state file.
  - Run: `terraform -chdir="${TF_DIR}" state list | head`
  - Teaching point: “Terraform code” (this repo) and “Terraform state” (GCS backend object) are separate. If you change `backend.hcl` `prefix`, you changed which state file Terraform is operating on.
