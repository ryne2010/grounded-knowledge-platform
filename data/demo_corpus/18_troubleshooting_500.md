# Troubleshooting 500s

## Common causes
- Container failed to start (wrong PORT, missing deps)
- Runtime error in API
- Database path/permissions issue

## Triage
1. Cloud Run revision logs
2. Confirm env vars (PUBLIC_DEMO_MODE, SQLITE_PATH)
3. Reproduce locally with Docker to isolate.
