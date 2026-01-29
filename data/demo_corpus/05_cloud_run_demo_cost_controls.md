# Cloud Run Demo — Keeping Costs Near $0

Cloud Run can scale to zero and has a free tier. For a personal portfolio demo, you can often keep monthly cost very low.

This document lists practical controls to avoid surprise bills.

## Use demo mode

Set:

- `PUBLIC_DEMO_MODE=1`

This disables uploads and forces extractive-only answers, so the demo cannot trigger external LLM charges.

## Scale to zero

Deploy with:

- `--min-instances=0`

so the service idles at zero when unused.

## Keep the architecture simple

For a public demo, avoid managed databases and storage if you don't need persistence.

This repo can bootstrap a small demo corpus on startup and store its index in SQLite.

## Limit abuse

- rate limit requests
- clamp `top_k`
- cap max question size

## Set budgets and alerts

Even with free tiers, you should set:

- a monthly budget
- alert thresholds

so you get notified long before any meaningful spend occurs.