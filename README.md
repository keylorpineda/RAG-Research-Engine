<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/hero-dark.svg">
  <img src="docs/assets/hero-light.svg" alt="Research Engine: answers from your documents, with the sources they come from, and no answer when the evidence is not there." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/keylorpineda/RAG-Research-Engine/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/keylorpineda/RAG-Research-Engine/ci.yml?branch=develop&style=flat-square&label=CI&color=2E7564" alt="CI"></a>
  <a href="https://github.com/keylorpineda/RAG-Research-Engine/actions/workflows/eval.yml"><img src="https://img.shields.io/github/actions/workflow/status/keylorpineda/RAG-Research-Engine/eval.yml?branch=develop&style=flat-square&label=benchmark&color=2E7564" alt="Benchmark"></a>
  <img src="https://img.shields.io/badge/Python-3.12-2E7564?style=flat-square" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Postgres-pgvector-2E7564?style=flat-square" alt="Postgres with pgvector">
  <img src="https://img.shields.io/badge/mypy-strict-2E7564?style=flat-square" alt="mypy strict">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2E7564?style=flat-square" alt="MIT license"></a>
</p>

Upload PDFs and notes, ask questions in English or Spanish, and get answers that cite the exact
passages they use. When the documents do not hold the answer, the engine refuses **before**
calling the language model instead of writing something plausible.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/results-dark.svg">
  <img src="docs/assets/results-light.svg" alt="Results: Recall@5 0.38 local dense, 0.53 local hybrid, 0.73 Cohere hybrid, 0.88 Cohere with rerank. At the default threshold the engine answers 91% of answerable questions and refuses 88% of unanswerable ones. Search over 50,000 chunks takes 10 ms instead of 39 s." width="100%">
</picture>

Every number above is produced by a benchmark in this repository (82 questions over 26 Python
Enhancement Proposals, English and Spanish) that runs on each pull request and fails if quality
drops. Method, full tables and experiments: [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/flow-dark.svg">
  <img src="docs/assets/flow-light.svg" alt="How it works. Ingest: upload, queue, chunk, embed, Postgres. Ask: the question goes to dense and lexical search, fused with RRF, optionally reranked; below the similarity threshold the engine does not answer, otherwise it answers with checked citations." width="100%">
</picture>

- **Hybrid retrieval.** pgvector (HNSW) and Postgres full-text search, fused with Reciprocal Rank
  Fusion; an optional Cohere reranker reorders the top 30.
- **A gate before the model.** Below the calibrated similarity threshold the answer is
  `insufficient_evidence` and no tokens are spent.
- **Checked citations.** The model cites numbered passages `[n]`; citations to passages it was
  not given are removed and reported.
- **A queue in Postgres.** Workers claim ingestion jobs with `FOR UPDATE SKIP LOCKED`, with
  leases, retries and idempotent re-ingestion.

Why each choice, and what it costs: [`docs/DECISIONS.md`](docs/DECISIONS.md) ·
code map: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Quick start

```bash
cp .env.example .env        # only GROQ_API_KEY is required
docker compose up --build   # Postgres + pgvector, API on :8000, one worker
```

```bash
curl -F "files=@paper.pdf" localhost:8000/api/upload
curl -s localhost:8000/api/query -H "Content-Type: application/json" -d '{"q": "What does the paper propose?"}'
```

Interactive API docs at <http://localhost:8000/docs>.

<details>
<summary><b>Responses</b></summary>

<br>

```json
{
  "answered": true,
  "answer": "Coroutines are declared with async def [1] and suspended with await [2].",
  "refs": [{ "n": 1, "filename": "pep-0492.rst", "chunkIndex": 4, "denseScore": 0.71, "lexicalScore": 0.12, "cited": true, "text": "..." }],
  "invalidCitations": [],
  "evidence": { "bestSimilarity": 0.71, "minSimilarity": 0.55 }
}
```

```json
{
  "answered": false,
  "answer": null,
  "reason": "insufficient_evidence",
  "refs": [],
  "evidence": { "bestSimilarity": 0.31, "minSimilarity": 0.55 }
}
```

</details>

<details>
<summary><b>Configuration</b></summary>

<br>

| Variable | Default | |
| :-- | :-- | :-- |
| `GROQ_API_KEY` | | Language model for the answers |
| `EMBEDDING_PROVIDER` | `local` | `local` (ONNX on the CPU, no key) or `cohere` |
| `RERANK_PROVIDER` | `none` | `cohere` reranks the top `RERANK_CANDIDATES` (30) |
| `MIN_SIMILARITY` | per model | Abstain below this best similarity (0.55 local, 0.60 Cohere) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200` | Characters |
| `COHERE_*_PER_MINUTE` | off | Token and call budgets for Cohere trial keys |
| `EMBEDDED_WORKER` | `false` | Run one worker inside the API process |

All settings: [`app/core/config.py`](app/core/config.py) · [`.env.example`](.env.example).

</details>

<details>
<summary><b>Development</b></summary>

<br>

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

Integration tests and the benchmark need Postgres with pgvector:

```bash
docker compose up -d postgres
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres uv run pytest
EVAL_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_eval uv run python -m eval.run
```

| Path | |
| :-- | :-- |
| `app/` | API, retrieval, answering, ingestion, worker |
| `migrations/` | Alembic, from the v1 schema |
| `eval/` · `bench/` | Retrieval benchmark · vector search latency |
| `web/` | Angular client: ask, library, benchmarks (`pnpm start`) |
| `docs/` | Benchmarks, architecture, decisions, these cards (`docs/assets/build.py`) |

Contributions: [`CONTRIBUTING.md`](.github/CONTRIBUTING.md) · security reports:
[`SECURITY.md`](.github/SECURITY.md) · roadmap: [project board](https://github.com/users/keylorpineda/projects/4).

</details>

## Limits

- The corpus is small (26 documents) and thresholds are calibrated on the same questions they are
  measured on: the numbers compare designs, they are not a promise on your documents.
- The API has no authentication; run it on a private network or behind an authenticating proxy.

---

<p align="center"><sub>© 2026 <a href="https://github.com/keylorpineda">Keylor Pineda</a> · Systems Engineering, Universidad Nacional de Costa Rica · <a href="LICENSE">MIT license</a></sub></p>
