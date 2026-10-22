# Design decisions

Short records of the choices that shape the engine: the context, what was decided, and what it
costs. Numbers come from [`BENCHMARKS.md`](BENCHMARKS.md).

## 1. Vectors live in Postgres (pgvector), not in a separate vector database

**Context.** v1 stored vectors as `JSONB` and scored them in a Python loop on every question:
39 seconds at 50,000 chunks.

**Decision.** `vector(N)` columns with an HNSW index, queried with `ORDER BY embedding <=> q`.

**Why.** Documents, chunks, jobs and the query log already live in Postgres, so filtering by
document status, deleting a document and its vectors, and backups are all one transaction in
one system. HNSW answers in about 10 ms at 50,000 chunks with the same top 10 as an exact
search.

**Cost.** Changing the embedding model changes the column size: it needs a migration and a
re-ingestion. A dedicated vector database would scale further, but this corpus size is far
from that limit.

## 2. Hybrid retrieval fused with RRF instead of a weighted score

**Context.** Dense retrieval blurs exact identifiers (`TypeVarTuple`, `__future__`, `572`).
Lexical retrieval cannot match a Spanish question to English text.

**Decision.** Run both and fuse them with Reciprocal Rank Fusion (`k = 60`).

**Why.** Cosine similarity and `ts_rank_cd` are on unrelated scales. A weighted sum would need
normalization and a tuned weight; RRF only uses positions and has one well-studied constant.
On the benchmark, hybrid beats both retrievers on every ranking metric. Lexical search is
excellent for English questions and weak for Spanish ones; dense search is the other way
around, and the fusion keeps the strengths of both.

**Cost.** Two queries per question instead of one (lexical adds about 30 ms).

## 3. Abstain on retrieval evidence, before calling the model

**Context.** v1 asked the model, at temperature 0.7, to "admit ignorance". Nothing checked
whether it did.

**Decision.** If the best cosine similarity is below `MIN_SIMILARITY`, return
`insufficient_evidence` without calling the model. The model can still refuse (`NO_ANSWER`)
when the passages are related but do not contain the answer.

**Why.** A threshold is a rule that can be calibrated and measured; a prompt instruction is a
request. It also saves a model call on every question the corpus cannot answer.

**Cost.** Similarity scales differ per embedding model, so the threshold is calibrated per
model, and some answerable questions are refused. The benchmark publishes the full trade-off
curve, not just one point.

## 4. Citations are numbers that the server checks

**Decision.** Passages are sent as `[1]..[n]`, the model cites by number, and the server
removes and reports any number that points to no passage.

**Why.** A filename in brackets cannot be verified. A number maps to exactly one chunk, so the
client can show the cited passage, and an invented citation becomes visible instead of
looking like a source.

## 5. The jobs table is the queue

**Context.** v1 polled for `PENDING` documents in a thread inside the API. Two replicas
ingested the same document twice; a crash left documents in `PROCESSING` forever.

**Decision.** Workers claim jobs with `FOR UPDATE SKIP LOCKED`, hold a lease, and retry with
exponential backoff.

**Why.** It gives exactly-once claiming, crash recovery and retries without adding Redis or a
broker, and the job state commits in the same transaction as the document state.

**Cost.** Polling (every 2 s by default) instead of push notifications; `LISTEN/NOTIFY` could
remove that delay later.

## 6. A local embedding model for tests and the benchmark

**Decision.** `EMBEDDING_PROVIDER=local`, the default, runs a multilingual ONNX model on the
CPU through `fastembed`. Cohere is one environment variable away.

**Why.** The engine, the test suite and the benchmark run without an embeddings key, so the
project starts with a single key (Groq, for the answers), and CI can check retrieval quality
on every pull request.

**Cost.** The small local model is weaker than Cohere's. The numbers in the README are for the
local model, so they are a floor, not the engine's best case.
