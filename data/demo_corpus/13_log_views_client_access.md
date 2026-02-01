# Client Observability Access with Log Views

## Problem
Clients often need access to logs/metrics **without** access to edit resources or view unrelated project logs.

## Pattern
- Route service logs into a dedicated log bucket.
- Create a **log view** filtered to `service_name=gkp-<env>`.
- Grant clients `roles/logging.viewAccessor` to the view (not project-wide logging.viewer).

This is a realistic enterprise pattern for regulated environments.
