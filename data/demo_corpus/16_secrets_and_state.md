# Secrets and Terraform State

## Principle
Terraform state is sensitive; avoid putting secret values into state.

## Pattern
- Terraform creates secret containers.
- Secret values are added via separate commands or CI secrets.
- Runtime service account gets secret accessor for only required secrets.

## Local auth vs CI
- Local: ADC (developer workflow)
- CI: WIF (keyless auth) for GitHub Actions
