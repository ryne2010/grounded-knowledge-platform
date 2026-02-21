# Non-goals

This repo is meant to feel production-grade, but it is intentionally scoped.

Decision record: `docs/DECISIONS/ADR-20260221-public-demo-and-deployment-model.md`

---

## Public demo non-goals (hard constraints)

- No uploads or connectors.
- No evaluation endpoints.
- No external LLM calls (extractive-only).
- No user accounts or login (anonymous only).
- No non-demo corpus data.

Rationale: keep the public URL safe, cheap, and hard to abuse.

---

## Product non-goals (overall)

### Not a full document management system
- No rich document editing workflow, approvals, or lifecycle management.
- No complex folder permissions model.
- No full-text document previewer comparable to a DMS.

### Not a chatbot with memory
- No long-term conversational memory across sessions (unless explicitly added later).
- No agentic browsing or autonomous actions.

### Not a compliance suite
- No built-in DLP scanning, PII detection, or legal holds in the baseline.
- No guarantee of compliance with any specific regime without additional controls.

### Not multi-tenant (by default)
- The primary boundary is **one GCP project per client**.
- In-app multi-tenancy is an optional future project, not a requirement.

### Not a large-scale search platform (yet)
- This repo targets “small-to-medium corpora” first.
- Billion-scale vector search or multi-region architecture is out of scope.

---

## Optional future enhancements (explicitly deferred)

- OIDC/IAP integration (auth mode beyond API keys)
- Workspace-aware multi-tenancy
- Advanced evaluation analytics (stat sig, cohort analysis)
- Edge WAF/CDN assumptions (Cloud Armor/Cloudflare) for the baseline demo
