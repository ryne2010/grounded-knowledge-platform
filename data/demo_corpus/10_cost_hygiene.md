# Cost Hygiene

## Keep the demo cheap
- Cloud Run: min instances 0, max instances 1
- No external LLM calls in public demo
- Avoid HTTP(S) Load Balancers for hobby demos
- Avoid Cloud DNS zones unless needed

## Artifact Registry cleanup
Use cleanup policies to avoid stale images accumulating.

## Logging
Logs can be a cost driver at scale. Keep INFO level and avoid verbose debug in public demos.
