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
calling the language model instead of writing something plausible. A web app shows each answer
next to its sources, and the abstentions with the evidence behind them.

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
- **Questions in Spanish too.** Dense search crosses languages; for full-text search the
  question is translated, which doubles Spanish lexical recall.
- **A queue in Postgres.** Workers claim ingestion jobs with `FOR UPDATE SKIP LOCKED`, with
  leases, retries and idempotent re-ingestion.
- **A web app.** Angular, in English and Spanish, light and dark: ask with linked citations,
  manage the library, and read the benchmarks.

Why each choice, and what it costs: [`docs/DECISIONS.md`](docs/DECISIONS.md) ·
code map: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Try it

The public demo answers questions about 26 Python Enhancement Proposals, the same corpus as the
benchmark. A few that work well:

| Ask | Answered from |
| :-- | :-- |
| How are coroutines declared, and what does await do? | PEP 492 |
| ¿Qué dice el Zen de Python sobre los errores? | PEP 20 |
| What is a dataclass's `__post_init__` for? | PEP 557 |
| What is the capital of Australia? | Nothing: the engine refuses and shows why |

It runs on free tiers: the first request after a quiet spell can take about a minute while the API
wakes up, and the demo allows 15 new questions a day (repeated ones are cached). The API is
documented at [`/docs`](https://research-engine-ed3a.onrender.com/docs).

## Quick start

```bash
cp .env.example .env        # only GROQ_API_KEY is required
docker compose up --build   # Postgres + pgvector, API on :8000, one worker
cd web && pnpm install && pnpm start   # web app on :4200, /api proxied to :8000
```

```bash
curl -F "files=@paper.pdf" localhost:8000/api/upload
curl -s localhost:8000/api/query -H "Content-Type: application/json" -d '{"q": "What does the paper propose?"}'
```

Interactive API docs at <http://localhost:8000/docs>.

No keys and no internet: run the answers on a local model too, with
`docker compose --profile local-llm up` and `LLM_PROVIDER=openai_compatible` (Ollama). Embeddings
are already local by default.

<details>
<summary><b>Responses</b></summary>

<br>

```json
{
  "answered": true,
  "answer": "Coroutines are declared with async def [1] and suspended with await [2].",
  "refs": [{ "n": 1, "filename": "pep-0492.rst", "chunkIndex": 4, "section": null, "denseScore": 0.71, "lexicalScore": 0.12, "cited": true, "text": "..." }],
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
| `GROQ_MODEL` | `openai/gpt-oss-120b` | With `GROQ_REASONING_EFFORT` (`low`) for reasoning models |
| `LLM_PROVIDER` | `groq` | `openai_compatible`: a local server (Ollama, llama.cpp) at `LLM_BASE_URL` |
| `EMBEDDING_PROVIDER` | `local` | `local` (ONNX on the CPU, no key) or `cohere` |
| `RERANK_PROVIDER` | `none` | `cohere` reranks the top `RERANK_CANDIDATES` (30) |
| `LEXICAL_TRANSLATION` | `false` | Translate non-English questions for full-text search (one model call, cached) |
| `MIN_SIMILARITY` | per model | Abstain below this best similarity (0.55 local, 0.60 Cohere) |
| `CHUNKING` | `window` | `sections`: split at headings first (better recall, recalibrate `MIN_SIMILARITY`) |
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
- The demo lowers the threshold to 0.45 so that it answers, and leans on the model's own refusal
  for the rest; [`docs/DEPLOY.md`](docs/DEPLOY.md) explains the trade-off.
- The API has no authentication; run it on a private network or behind an authenticating proxy.
  The demo turns uploads off and caps questions per day and per visitor instead.

---

<p align="center"><sub>© 2026 <a href="https://github.com/keylorpineda">Keylor Pineda</a> · Systems Engineering, Universidad Nacional de Costa Rica · <a href="LICENSE">MIT license</a></sub></p>
