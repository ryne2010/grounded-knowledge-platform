# Public Demo Corpus — Welcome

This repository contains a small **safe demo corpus** designed to be hosted publicly.
It is intentionally free of confidential data, credentials, and client-specific details.

## What this demo is

The **Grounded Knowledge Platform** is a reference implementation of a "citations-first" knowledge system:

- Users ask questions.
- The system retrieves relevant chunks from documents.
- The system answers **using only retrieved evidence**.
- Every answer includes **citations** that point back to the supporting chunks.

## What you can try in the live demo

In the public live demo (`PUBLIC_DEMO_MODE=1`):

- Ask questions about the documents in this corpus.
- See citations and click through the sources.
- Observe refusal behavior when evidence is weak.

Uploads are disabled in demo mode.

## Why the demo is read-only

Public demos are targets for misuse (prompt injection attempts, malicious file uploads, and cost abuse).
Demo mode disables uploads and external LLM calls and enables basic rate limiting.

## Example questions

- "What is a grounded knowledge system?"
- "How does hybrid retrieval work in this repo?"
- "How do you keep a Cloud Run demo low-cost?"
- "What security controls matter for confidential documents?"
