export const DEMO_SUGGESTED_QUERIES = [
  'What reliability guardrails are recommended for Cloud Run deployments?',
  'Why does this architecture use Cloud SQL Postgres with pgvector?',
  'How does hybrid retrieval combine lexical and vector signals?',
  'What controls keep the public demo safe by default?',
  'How should I verify citations before trusting an answer?',
  'What does add/update-only mean for GCS connector sync?',
]

export type GuidedTourStep = {
  id: string
  target: string
  title: string
  description: string
}

export const DEMO_GUIDED_TOUR_STEPS: GuidedTourStep[] = [
  {
    id: 'mode',
    target: 'demo-badge',
    title: 'Demo mode badge',
    description:
      'This badge confirms public read-only mode. The demo uses only the bundled corpus and keeps privileged actions disabled.',
  },
  {
    id: 'query',
    target: 'query-input',
    title: 'Ask a question',
    description: 'Enter a question here, or run one of the suggested demo queries to see grounded answers quickly.',
  },
  {
    id: 'citations',
    target: 'citations-list',
    title: 'Verify citations',
    description: 'Citations appear with each answer turn. Open cited context and confirm the quoted snippet matches the source.',
  },
  {
    id: 'docs',
    target: 'doc-source-viewer',
    title: 'Inspect docs and sources',
    description:
      'Use Docs/Search to inspect the source corpus directly. Ingest/connectors stay disabled in public demo mode for safety.',
  },
  {
    id: 'refusal',
    target: 'refusal-behavior',
    title: 'Understand refusals',
    description:
      'If evidence is weak or safety policy is triggered, the system refuses instead of guessing. Refusal reasons are surfaced in the UI.',
  },
]
