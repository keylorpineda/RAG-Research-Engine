# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2026-10-22

Milestone **v2.1 — Web app**, and everything the public demo (v2.2) needs short of the
accounts.

### Added

- Angular web app in `web/` (pnpm, standalone, zoneless): dark and light themes, English and
  Spanish, responsive down to 360 px (#39).
- Library: drag-and-drop uploads with per-file progress and client-side checks, live document
  status, filters, retry, and deletes with an undo window (#40).
- Ask: answers with `[n]` citations linked to their passages and scores, an evidence meter, and
  an abstention card that explains each reason (#41).
- Benchmarks page generated from `eval/results` (#41) and inline SVG illustrations (#42).
- API: `chunkCount` on documents; `uploadsEnabled`, `maxUploadMb` and `maxFilesPerUpload` on
  `/api/health`; `UPLOADS_ENABLED=false` turns uploads off for a public demo (#40).
- Public demo limits, all off by default: a daily question cap counted in the database, a
  per-client hourly limit, and a cache for repeated questions; the web app shows the questions
  left and words the limits in the visitor's language (#44).
- Deployment: `render.yaml`, `web/vercel.json`, a single-VM setup with Caddy for Oracle Cloud
  (`deploy/oracle/`), `python -m eval.seed` to preload the PEPs, and `docs/DEPLOY.md` (#44).

### Fixed

- The Dockerfile had literal `
` sequences in two instructions; the image now builds, serves on
  `$PORT`, applies migrations on start and can skip the local model (`EXTRAS=none`) (#44).
- A `.dockerignore` keeps `.env`, `.venv` and `node_modules` out of the build context (#44).

### Removed

- The CustomTkinter desktop client (`desktop/`, `gui.py` and the `gui` extra): the web app
  covers uploads, documents and questions (#43).

## [2.0.0] - 2026-10-22

Milestone **v2.0 — Measured retrieval**: fix the retrieval bugs, move vectors into pgvector,
add hybrid search and abstention, and prove every change with a reproducible benchmark.

### Added

- Cohere results: hybrid + rerank Recall@5 0.879; abstention threshold calibrated at 0.60;
  optional token and call budgets for trial keys (#29, #33).
- Reproducible retrieval benchmark: 26 PEPs pinned by commit, 66 answerable questions
  (English and Spanish) with evidence quotes and 16 unanswerable ones, Recall@k, MRR, nDCG,
  abstention trade-off and latency, run in CI with a regression gate (`eval/`) (#10).
- Retrieval-gated abstention: the engine answers `insufficient_evidence` without calling the
  model when the best similarity is below `MIN_SIMILARITY`, calibrated per embedding model (#8).
- Numbered passages and verified citations: invalid `[n]` markers are removed and reported (#8).
- Hybrid retrieval: Postgres full-text search fused with dense search by Reciprocal Rank Fusion,
  `mode` field on queries (#6).
- Optional Cohere rerank stage (`RERANK_PROVIDER=cohere`) (#7).
- Ingestion worker process (`python -m app.worker`) with a `SKIP LOCKED` job queue, leases,
  retries with backoff, `POST /api/documents/{id}/reingest` and `GET /api/health` (#9).
- Local embedding provider (`EMBEDDING_PROVIDER=local`, fastembed, no API key) (#3).
- Alembic migrations, from the v1 schema to the current one (#5).
- Vector search latency benchmark (`bench/vector_search.py`) (#5).
- `uv` project with a lockfile, Ruff, mypy strict, pytest, CI, Dependabot, issue and PR
  templates, contributing guide, security policy, code of conduct and license (#1, #15).

### Changed

- Embeddings are stored in `vector(N)` columns with an HNSW index and searched inside Postgres;
  50,000 chunks: 38,972 ms → 10.5 ms (#5).
- `POST /api/query` returns `answered`, `reason`, numbered `refs` with per-retriever scores,
  `invalidCitations` and `evidence`. `threshold` is replaced by `minSimilarity` (#8).
- The language model runs at temperature 0 with a short grounded prompt (#8).
- Every error response is `{"error": {"code", "message", "requestId"}}` (#2).
- The desktop client shows abstentions, numbered citations and the retrieval mode (#11).
- README rebuilt around three cards (hero, results, how it works) in the *Deep Ink* palette of the
  web app design, generated from the committed results (#47).
- Database driver: psycopg 3 (`postgresql://` URLs keep working) (#5).
- `EMBEDDING_PROVIDER` defaults to `local`; the Docker image includes the local model runtime
  and keeps the model in a `models` volume. Set `EMBEDDING_PROVIDER=cohere` to keep using
  Cohere (#27).

### Fixed

- Path traversal on upload: files are stored under server-generated names (#2).
- Internal errors and provider responses are no longer returned to clients (#2).
- Questions were embedded with Cohere's `search_document` input type instead of
  `search_query` (#3).
- Upload-time recency weighting discarded relevant passages and let weak ones through (#4).
- Two API replicas could ingest the same document twice; a crash left documents stuck in
  `PROCESSING` (#9).

### Removed

- `init.sql` (replaced by migrations), `COHERE_EMBEDDING_INPUT_TYPE`,
  `INGESTION_POLL_INTERVAL_MS` and the ingestion thread inside the API.

### Upgrading from 1.x

v1 always used Cohere. To keep your vectors, set `EMBEDDING_PROVIDER=cohere` before migrating;
with the new default (`local`) every document is queued and embedded again with the local model.

```bash
alembic stamp 0001        # mark the existing v1 schema
alembic upgrade head      # vectors move to pgvector; documents with other dimensions are requeued
python -m app.worker      # start at least one worker
```

## [1.0.0] - 2026-04-04

First prototype: FastAPI, Postgres with JSONB vectors, Cohere embeddings, Groq answers and the
CustomTkinter desktop client.

[Unreleased]: https://github.com/keylorpineda/RAG-Research-Engine/compare/v2.1.0...develop
[2.1.0]: https://github.com/keylorpineda/RAG-Research-Engine/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/keylorpineda/RAG-Research-Engine/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/keylorpineda/RAG-Research-Engine/releases/tag/v1.0.0
