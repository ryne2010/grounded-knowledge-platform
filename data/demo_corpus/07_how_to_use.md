# How to Use (Local)

## Start services
1. Start the API (FastAPI).
2. Start the UI (React + TanStack Router).
3. Ingest documents into the index.

## Ask questions
Use the Ask page. In local mode you can enable **retrieval debug** to see:
- which chunks were retrieved
- score breakdown (lexical / vector)
- citations used

## Safety regression
Run the safety suite:
- prompt injection
- refusal behavior

## Reindexing
If you change the embeddings backend/model, delete the index and re-ingest:
- remove `data/index.sqlite`
- re-run ingest
