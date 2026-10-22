# Benchmarks

Every number in the README comes from this page, and every number on this page comes from a
script in the repository that you can run again.

- [Retrieval quality](#retrieval-quality)
- [Abstention](#abstention)
- [Cohere embeddings](#cohere-embeddings)
- [Experiments: chunk size and embedding model](#experiments-chunk-size-and-embedding-model)
- [Experiment: translating questions for lexical search](#experiment-translating-questions-for-lexical-search)
- [Vector search latency](#vector-search-latency)

## Retrieval quality

`eval/run.py` ingests the corpus with the real pipeline (Postgres, pgvector, the local
embedding model) and asks every question in each retrieval mode.

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Right PEP in top 5 | Recall@5 EN | Recall@5 ES | p50 |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| Dense | 0.167 | 0.379 | 0.485 | 0.264 | 0.280 | 0.955 | 0.361 | 0.400 | 99 ms |
| Lexical | 0.136 | 0.455 | 0.561 | 0.275 | 0.323 | 0.818 | 0.667 | 0.200 | 26 ms |
| **Hybrid** | **0.227** | **0.530** | **0.667** | **0.350** | **0.381** | **0.970** | 0.583 | **0.467** | 139 ms |

**Corpus.** 26 Python Enhancement Proposals (820 KiB, 1,240 chunks of 1,000 characters),
pinned to commit `3b0eaa2` of [python/peps](https://github.com/python/peps) and verified by
SHA-256 (`eval/corpus.lock.json`). PEPs are public domain or CC0.

**Questions** (`eval/questions.jsonl`, built and checked by `eval/build_questions.py`).
- 66 answerable questions: 36 in English and 30 in Spanish, over English text. Each one names
  its PEP and a short evidence quote that the build script verifies against the source.
- 16 unanswerable questions. 10 are off-topic; 6 are about Python but outside these PEPs
  (WSGI, twine, wheel names, logging configuration…).

**What counts as a hit.** A retrieved chunk from the expected PEP that contains the evidence
quote (case and whitespace normalized). This is stricter than "a chunk from the right
document", which is reported separately as *Right PEP in top 5*.

**Reading the table.**
- Hybrid is the best mode on every overall metric.
- Lexical search is the best for English questions (0.667), because PEPs are full of exact
  identifiers, and the worst for Spanish ones (0.200), because a Spanish question shares
  almost no words with English text.
- Dense search is the only one that crosses languages.
- RRF keeps most of both: the right PEP is in the top 5 for 97% of the questions, and the
  exact passage for 53%.

## Abstention

The gate compares the best dense similarity with a threshold τ. Answerable questions should
pass, unanswerable ones should not.

| τ | Answerable answered | Unanswerable refused | Python-adjacent refused | Abstention precision |
| --: | --: | --: | --: | --: |
| 0.35 | 1.000 | 0.562 | 0.000 | 1.000 |
| 0.45 | 1.000 | 0.625 | 0.167 | 1.000 |
| 0.50 | 0.970 | 0.625 | 0.167 | 0.833 |
| **0.55** | **0.909** | **0.875** | **0.833** | 0.700 |
| 0.60 | 0.682 | 0.938 | 0.833 | 0.417 |
| 0.65 | 0.379 | 1.000 | 1.000 | 0.281 |

**τ = 0.55** maximizes the mean of the two rates (balanced accuracy 0.892) and is the default
for the local model. Off-topic questions are easy to refuse at any reasonable τ. The
Python-adjacent ones are the real test: they sit close to the corpus, and only from 0.55 up
are most of them refused. Above 0.60 the gate starts refusing questions the corpus can answer.
*Abstention precision* is the share of refusals that were right; it counts the questions that
were refused by mistake.

The threshold is calibrated on the questions it is evaluated on (82 in total), so it is a
starting point for other corpora, not a guarantee. Each embedding model needs its own value:
`DEFAULT_MIN_SIMILARITY` in `app/core/config.py`.

## Cohere embeddings

The same benchmark with `embed-multilingual-v3.0` (1,024 dimensions) and, for the last row, the
`rerank-v3.5` cross-encoder over the top 30 hybrid candidates. Run with a trial key.

| Mode | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Right PEP in top 5 | Recall@5 EN | Recall@5 ES | p50 |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| Dense | 0.409 | 0.712 | 0.818 | 0.536 | 0.567 | 1.000 | 0.806 | 0.600 | 206 ms |
| Lexical | 0.136 | 0.455 | 0.561 | 0.275 | 0.323 | 0.818 | 0.667 | 0.200 | 9 ms |
| Hybrid | 0.379 | 0.727 | 0.788 | 0.509 | 0.534 | 1.000 | 0.861 | 0.567 | 218 ms |
| **Hybrid + rerank** | 0.712 | 0.879 | 0.894 | 0.779 | 0.777 | 1.000 | 0.917 | 0.833 | 431 ms |

- **The embedding model matters most.** Dense Recall@5 goes from 0.379 (local MiniLM) to 0.712,
  and every question finds its PEP in the top 5.
- **Reranking is the largest single gain:** hybrid + rerank puts the exact passage first for 71%
  of the questions (MRR 0.779) and closes most of the gap in Spanish (0.833), for about 210 ms
  more per question.
- **Hybrid adds less on top of a strong dense model** (+1.5 points of Recall@5), and with Cohere
  it slightly lowers MRR: the lexical list pushes some exact passages from first to second.
  Rerank recovers it.
- Lexical numbers are identical to the local run, as expected: it does not use embeddings.

**Abstention with Cohere.**

| τ | Answerable answered | Unanswerable refused | Python-adjacent refused | Abstention precision |
| --: | --: | --: | --: | --: |
| 0.35 | 1.000 | 0.312 | 0.000 | 1.000 |
| 0.40 | 1.000 | 0.438 | 0.000 | 1.000 |
| 0.45 | 1.000 | 0.562 | 0.000 | 1.000 |
| 0.50 | 0.970 | 0.688 | 0.333 | 0.846 |
| 0.55 | 0.879 | 0.750 | 0.333 | 0.600 |
| 0.60 | 0.727 | 1.000 | 1.000 | 0.471 |
| 0.65 | 0.485 | 1.000 | 1.000 | 0.320 |

The default for Cohere is **τ = 0.60**, the threshold with the best balanced accuracy (0.864): it
refuses every unanswerable question, including the six Python-adjacent ones, and answers 73% of
the answerable ones. Cohere's similarities sit higher and closer together than MiniLM's, so the
two groups overlap more. If answering more matters more than refusing everything, `MIN_SIMILARITY=0.50`
answers 97% and still refuses 69%.

```bash
EMBEDDING_PROVIDER=cohere COHERE_API_KEY=... COHERE_TOKENS_PER_MINUTE=90000   COHERE_EMBED_REQUESTS_PER_MINUTE=90 COHERE_RERANK_REQUESTS_PER_MINUTE=10   EVAL_DATABASE_URL=... uv run python -m eval.run --rerank --tag cohere
```

## Experiments: chunk size and embedding model

Same questions and corpus, one change at a time (`--tag` reports in `eval/results/`).

| Variant | Chunks | Ingest | Dense R@5 | Hybrid R@5 | Hybrid MRR | Hybrid R@5 ES | Query p50 | Suggested τ |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: |
| **MiniLM, 1,000 chars (default)** | 1,240 | 4 min | 0.379 | 0.530 | 0.350 | 0.467 | 139 ms | 0.55 |
| MiniLM, 500 chars | 2,523 | 8 min | 0.515 | 0.515 | 0.394 | 0.267 | 141 ms | 0.57 |
| mpnet-base, 1,000 chars | 1,240 | 29 min | 0.439 | 0.561 | 0.334 | 0.500 | 284 ms | 0.52 |

- **Smaller chunks** help dense search a lot (+14 points of Recall@5), because a short chunk is
  about one thing, and they put the right passage first more often (hybrid MRR 0.394). But
  hybrid Recall@5 does not improve and Spanish questions lose 20 points: shorter chunks carry
  fewer words for the lexical side to match, and twice as many chunks compete for the top 5.
- **A bigger embedding model** (mpnet, 768 dimensions) adds 3 points of hybrid Recall@5 and
  helps Spanish. In exchange, ingestion is 7 times slower on a CPU, queries take twice as long,
  and MRR is slightly lower.
- **Default:** MiniLM with 1,000-character chunks. It is the best balance on this corpus and
  keeps the CI benchmark under 10 minutes. Both alternatives are one environment variable
  away (`CHUNK_SIZE`, `LOCAL_EMBEDDING_MODEL`).

**Reproduce.**

```bash
EVAL_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_eval uv run python -m eval.run
CHUNK_SIZE=500 CHUNK_OVERLAP=100 EVAL_DATABASE_URL=... uv run python -m eval.run --tag minilm-500
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2 \
  EVAL_DATABASE_URL=... uv run python -m eval.run --tag mpnet-1000
```

With Cohere, see the command in [Cohere embeddings](#cohere-embeddings): it adds the trial-key
limits so ingestion and reranking wait instead of failing.

The runner wipes the database it is given and refuses any database whose name does not contain
`eval`, `test` or `bench`. CI runs it on every pull request that touches `app/`, `eval/` or
`migrations/`, and fails if hybrid or dense Recall@5, or the abstention balanced accuracy,
drop more than 3 points below `eval/results/baseline.json`.

## Experiment: translating questions for lexical search

Full-text search matches words, and the PEPs are in English: a Spanish question shares almost
none of them. With `LEXICAL_TRANSLATION=true` the engine asks the language model for an English
version of non-English questions and uses it **only** for full-text search; dense search, the
reranker, the abstention gate and the answer keep the original question. English questions are
detected and left alone.

MiniLM, 1,000-character chunks, translations by `openai/gpt-oss-120b` on Groq
(`eval/results/minilm-translation.json`):

| Mode | Recall@5 | Recall@10 | MRR@10 | Recall@5 EN | Recall@5 ES | p50 |
| :-- | --: | --: | --: | --: | --: | --: |
| lexical | 0.455 | 0.561 | 0.275 | 0.667 | 0.200 | 13 ms |
| lexical + translation | 0.545 | 0.667 | 0.373 | 0.667 | **0.400** | 16 ms |
| hybrid | 0.530 | 0.667 | 0.350 | 0.583 | 0.467 | 52 ms |
| hybrid + translation | **0.545** | **0.727** | **0.376** | 0.583 | **0.500** | 121 ms |

- Spanish lexical Recall@5 doubles (0.200 to 0.400). English numbers do not move, as they
  should: those questions are never translated.
- Hybrid gains less (+3 points in Spanish, +6 points of Recall@10 overall), because its dense
  half already crossed languages.
- The cost is one model call per new non-English question (cached afterwards); the median
  latency above includes it. If the call fails, the original question is searched.
- **Default:** off, so the engine works without a language model for retrieval. The demo
  configurations turn it on.

**Reproduce.** `EVAL_DATABASE_URL=... uv run python -m eval.run --translate --tag minilm-translation`
(needs `GROQ_API_KEY`).

## Vector search latency

How long it takes to find the 10 nearest chunks to a question, by corpus size.

| Chunks | v1 Python scan | pgvector exact | pgvector HNSW | HNSW recall@10 |
| --: | --: | --: | --: | --: |
| 1,000 | 783.9 ms | 3.19 ms | 3.94 ms | 1.000 |
| 10,000 | 7,558.2 ms | 10.87 ms | 4.24 ms | 1.000 |
| 50,000 | 38,972.3 ms | 189.64 ms | 10.46 ms | 1.000 |

Median (p50) over 30 queries (5 for the v1 scan). p95 values are in
[`benchmarks/vector_search.json`](benchmarks/vector_search.json).

- **v1 Python scan**: what v1 did on every question. Load every vector from a `JSONB` column,
  compute cosine similarity in a Python loop, sort. It grows linearly and is already unusable at
  10,000 chunks (about 10 MB of text).
- **pgvector exact**: the same query in Postgres without the index (`enable_indexscan = off`):
  still linear, but 200 to 700 times faster than the Python loop.
- **pgvector HNSW**: the index used by the engine (`m = 16`, `ef_construction = 64`,
  `ef_search = 100`). Latency stays almost flat and it found the same top 10 as the exact search.

**Setup.** 384-dimension vectors (the size of the local embedding model). Postgres 16.2,
pgvector 0.6.2, 12th-gen Intel laptop CPU (12 threads), Windows 11, database on the same machine.

**Data.** Synthetic vectors grouped around topics (`n / 50` centroids plus noise), and questions
placed near stored vectors, which is how real embeddings behave. On independent Gaussian vectors
HNSW recall@10 drops to 0.65 at 10,000 and 0.20 at 50,000: in 384 dimensions all their distances
are nearly equal, so the "nearest" neighbors are noise. That case says little about text
retrieval, but it is the reason recall is measured here instead of assumed.

**Reproduce.**

```bash
BENCH_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_bench \
  uv run python -m bench.vector_search
```

The script creates and drops its own tables in the database you point it at.
