# Drift Detection

## Why
Manual console changes can cause drift and inconsistent environments.

## Pattern
- Scheduled job runs `terraform plan -detailed-exitcode`
- Notify on drift
- Fix by applying from code, not clicking in console.

## For demos
Drift detection is still valuable: it proves operational discipline.
