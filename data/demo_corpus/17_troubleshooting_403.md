# Troubleshooting 403s

## Common causes
- Cloud Run invoker permission missing
- Service account actAs missing
- Secret access missing (Secret Manager accessor)
- Wrong project/region configuration

## Triage
1. Confirm which identity is calling (user vs service account).
2. Check IAM bindings at the correct scope (project vs resource).
3. Inspect Cloud Run logs and request IDs.
