# Benchmarks

Every number in the README comes from this page, and every number on this page comes from a
script in the repository that you can run again.

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
