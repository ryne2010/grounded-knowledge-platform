# Retrieval pipeline

Retrieval is designed to be:

- **verifiable** (citations-first)
- **hybrid** (lexical + vector)
- **safe** (prompt-injection detection and refusal)
- **fast enough** for small-to-medium corpora (Postgres baseline)

---

## Query flow

1) **Input sanitation**
   - normalize whitespace and apply conservative token limits
   - detect prompt-injection attempts (defense in depth)

2) **Retrieve candidates**
   - **Lexical**: Postgres full-text search (FTS) over `chunks.text`
   - **Vector**: pgvector cosine distance over `embeddings.vec`
   - Merge and rerank (hybrid strategy)

3) **Assemble evidence pack**
   - pick top-K chunks
   - compute citation snippets and offsets

4) **Answer**
   - Public demo: extractive answer only (quotes + light glue)
   - Private: optional richer LLM providers (behind auth)

5) **Refusal**
   - If evidence is weak/insufficient, refuse with a clear explanation.

---

## “Citations first” invariant

- Responses must include citations that map to retrieved chunks.
- If citations can’t be produced, the system refuses rather than hallucinating.

---

## Observability hooks

Retrieval should emit (planned / partially implemented):
- retrieval latency (lexical/vector/rerank)
- hit counts and score distributions
- refusal rates and reasons (without logging sensitive content)

