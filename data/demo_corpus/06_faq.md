# FAQ

## What is this?
A grounded knowledge base that answers questions **only using indexed sources** and returns citations.

## Does it use an LLM?
- **Local/private:** can use a local model (Ollama) for fluent summaries.
- **Public demo:** defaults to **extractive-only** (no model calls) for safety and low cost.

## How do I prevent hallucinations?
- Require citations for answers.
- Refuse when evidence is insufficient.
- Run prompt-injection regression tests.
- Treat retrieved text as **untrusted input**.

## What data can I ingest?
Markdown, plain text, and PDFs (OCR optional for scanned PDFs).

## How do I keep costs near $0 on GCP?
Use Cloud Run with:
- min instances = 0 (scale to zero)
- max instances = 1 (hard cap)
- no load balancer
- avoid VPC connector unless needed
