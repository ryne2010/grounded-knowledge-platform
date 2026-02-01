# RBAC and Governance

## Governance metadata
Documents can carry metadata like:
- classification tags (e.g., public/confidential)
- retention policy flags

## Minimal RBAC model
- JWT claim contains `allowed_tags`.
- Query-time filters enforce access:
  only documents whose tags intersect with allowed tags are eligible for retrieval/citation.

## Public demo
RBAC is typically disabled for public demo; access is controlled by using only public documents and disabling uploads.
