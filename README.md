<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/hero-dark.svg">
  <img src="docs/assets/hero-light.svg" alt="RAG Research Engine: answers from your documents, with sources you can check, and a clear I don't know when the evidence is not there" width="100%">
</picture>

<p align="center">
  <a href="https://github.com/keylorpineda/RAG-Research-Engine/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/keylorpineda/RAG-Research-Engine/ci.yml?branch=develop&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/keylorpineda/RAG-Research-Engine/actions/workflows/eval.yml"><img src="https://img.shields.io/github/actions/workflow/status/keylorpineda/RAG-Research-Engine/eval.yml?branch=develop&style=flat-square&label=benchmark" alt="Benchmark"></a>
  <img src="https://img.shields.io/badge/Python-3.12-0D9488?style=flat-square" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Postgres-pgvector%20%C2%B7%20HNSW-0D9488?style=flat-square" alt="Postgres with pgvector">
  <img src="https://img.shields.io/badge/types-mypy%20strict-0D9488?style=flat-square" alt="mypy strict">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0D9488?style=flat-square" alt="MIT license"></a>
</p>

Ask a question about your PDFs and notes and get an answer that cites the exact passages it
used. When those documents do not contain the answer, the engine says so **before** calling
the language model, instead of writing something plausible. Every number on this page comes
from a benchmark in this repository that runs in CI.

## Results

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/recall-dark.svg">
  <img src="docs/assets/recall-light.svg" alt="Recall at 5: dense 0.38, lexical 0.46, hybrid 0.53. Lexical reaches 0.67 in English but 0.20 in Spanish; hybrid keeps 0.58 and 0.47." width="100%">
</picture>

| Retrieval | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Right PEP in top 5 |
| :-- | --: | --: | --: | --: | --: | --: |
| Dense (pgvector) | 0.167 | 0.379 | 0.485 | 0.264 | 0.280 | 0.955 |
| Lexical (full-text) | 0.136 | 0.455 | 0.561 | 0.275 | 0.323 | 0.818 |
| **Hybrid (RRF)** | **0.227** | **0.530** | **0.667** | **0.350** | **0.381** | **0.970** |

66 questions about 26 Python Enhancement Proposals, 36 in English and 30 in Spanish. A hit means
a retrieved chunk **contains the quote that answers the question**, not just any chunk from the
right document. Hybrid beats both retrievers on every overall metric: lexical search is strong on
English identifiers and fails on Spanish questions over English text, dense search is the
other way around, and the fusion keeps both.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/abstention-dark.svg">
  <img src="docs/assets/abstention-light.svg" alt="Threshold trade-off: at 0.55 the engine answers 91% of answerable questions and refuses 88% of unanswerable ones." width="100%">
</picture>

With the calibrated threshold (0.55), the engine answers **91%** of the questions the corpus can
answer and refuses **88%** of those it cannot, including 5 of the 6 tricky ones about Python
topics the corpus does not cover. Refused questions never reach the language model.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/latency-dark.svg">
  <img src="docs/assets/latency-light.svg" alt="Top-10 search over 50,000 chunks: 39 s in v1, 190 ms with an exact pgvector scan, 10 ms with HNSW." width="100%">
</picture>

Full numbers, setups, the chunk-size and embedding-model experiments, and how to reproduce
everything: [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md).

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/query-dark.svg">
  <img src="docs/assets/query-light.svg" alt="The question goes to dense and lexical search, fused with RRF, then a gate: below the threshold the engine abstains, otherwise it answers with numbered citations." width="100%">
</picture>

- **Hybrid retrieval.** Dense search through a pgvector HNSW index and Postgres full-text
  search run side by side and are fused with Reciprocal Rank Fusion. An optional Cohere
  reranker can reorder the top 30.
- **Abstention gate.** If no passage is similar enough to the question, the answer is
  `insufficient_evidence` and the model is not called. The threshold is calibrated per
  embedding model on the benchmark.
- **Checked citations.** Passages are numbered, the model cites them as `[n]` at temperature 0,
  and the server removes and reports any number that points to no passage.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/ingest-dark.svg">
  <img src="docs/assets/ingest-light.svg" alt="Upload, queue, chunk, embed, Postgres." width="100%">
</picture>

- **A queue in Postgres.** Uploads become jobs; any number of `python -m app.worker` processes
  claim them with `FOR UPDATE SKIP LOCKED`, under a lease that another worker takes over if one
  crashes, with retries and backoff.
- **Safe uploads.** Server-generated file names, a size limit enforced while streaming, and
  content checks (PDF magic bytes, no binary data in text files).

Architecture and code map: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Why each choice was
made, and what it costs: [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Quick start

```bash
cp .env.example .env               # only GROQ_API_KEY is required
docker compose up --build          # Postgres + pgvector, API on :8000, one worker
```

```bash
curl -F "files=@paper.pdf" localhost:8000/api/upload
curl -s localhost:8000/api/query -H "Content-Type: application/json" \
  -d '{"q": "What does the paper propose?", "mode": "hybrid"}'
```

<details>
<summary><b>Example responses</b></summary>

<br>

```json
{
  "answered": true,
  "answer": "Coroutines are declared with async def [1] and suspended with await [2].",
  "reason": null,
  "refs": [
    { "n": 1, "filename": "pep-0492.rst", "chunkIndex": 4, "denseScore": 0.71, "lexicalScore": 0.12, "cited": true, "text": "..." }
  ],
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
  "invalidCitations": [],
  "evidence": { "bestSimilarity": 0.31, "minSimilarity": 0.55 }
}
```

Interactive API docs: <http://localhost:8000/docs>.

</details>

<details>
<summary><b>Desktop client</b></summary>

<br>

```bash
uv sync --extra gui
RAG_API_URL=http://localhost:8000/api uv run python gui.py
```

Upload files, follow their status, ask questions in hybrid, dense or lexical mode, and see each
cited passage next to the answer. Abstentions are shown with their reason.

</details>

<details>
<summary><b>Configuration</b></summary>

<br>

| Variable | Default | |
| :-- | :-- | :-- |
| `EMBEDDING_PROVIDER` | `local` | `local` (ONNX on the CPU, no key) or `cohere` (needs `COHERE_API_KEY`) |
| `GROQ_API_KEY` | | Language model for the answers |
| `MIN_SIMILARITY` | calibrated per model | Abstain below this best cosine similarity |
| `RERANK_PROVIDER` | `none` | `cohere` reranks the top `RERANK_CANDIDATES` (30) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200` | Characters |
| `HNSW_EF_SEARCH` | `100` | Higher is more accurate and slower |
| `EMBEDDED_WORKER` | `false` | Run one worker inside the API process |
| `JOB_MAX_ATTEMPTS` | `5` | Retries before a document is marked `ERROR` |

Every setting is in [`app/core/config.py`](app/core/config.py).

</details>

## Development

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

Integration tests need a Postgres with pgvector (`TEST_DATABASE_URL`); the benchmark needs a
database it is allowed to wipe (`EVAL_DATABASE_URL`):

```bash
docker compose up -d postgres
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres uv run pytest
EVAL_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_eval uv run python -m eval.run
```

| Path | Contents |
| :-- | :-- |
| `app/` | API, retrieval, answering, ingestion, worker |
| `migrations/` | Alembic migrations (starting from the v1 schema) |
| `eval/` | Benchmark corpus, questions and runner |
| `bench/` | Vector search latency benchmark |
| `desktop/`, `gui.py` | Desktop client |
| `docs/` | Architecture, decisions, benchmarks, illustrations |

Contributions are welcome: read [`CONTRIBUTING.md`](.github/CONTRIBUTING.md). Retrieval changes
come with benchmark numbers. Report security issues through the
[private advisory form](https://github.com/keylorpineda/RAG-Research-Engine/security/advisories/new),
see [`SECURITY.md`](.github/SECURITY.md).

## Limits

- The benchmark corpus is small (26 documents, 1,240 chunks) and the threshold is calibrated on
  the same 82 questions it is evaluated on. The numbers compare designs; they do not promise
  the same values on your documents.
- The committed numbers use the small local embedding model, so they are a floor. Cohere's
  model needs its own threshold: calibrate it with `eval.run` on your data.
- The API has no authentication: run it on a private network or behind an authenticating proxy.

## Author

Built by [Keylor Pineda](https://github.com/keylorpineda), Systems Engineering student at the
Universidad Nacional de Costa Rica (UNA).

## License

[MIT](LICENSE) © 2025 Keylor Pineda
