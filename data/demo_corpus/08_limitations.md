# Limitations and Design Choices

## Public demo posture
The public demo is intentionally conservative:
- uploads disabled
- eval endpoints disabled
- extractive-only answers
- rate limiting enabled

This avoids data exfiltration, unexpected costs, and abuse.

## Local-only LLM
For confidential corpora, run an LLM locally (Ollama) and keep all data on-device/network.

## Retrieval quality depends on corpus quality
Short, well-structured docs with clear headings and keywords improve retrieval and grounded answers.
