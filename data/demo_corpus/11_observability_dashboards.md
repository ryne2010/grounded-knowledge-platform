# Observability (Dashboards)

## What we monitor
- request count
- latency (p50/p95)
- 4xx/5xx rate
- cold starts (proxy via latency + instance count)

## Staff-level posture
Dashboards and alerts should be **reproducible**:
- managed as code
- consistent across environments (`dev/stage/prod`)
