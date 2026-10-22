"""Vector search latency: the v1 Python scan vs pgvector (exact and HNSW).

    BENCH_DATABASE_URL=postgresql://... uv run python -m bench.vector_search

The database is used as scratch space: the script creates and drops its own tables.
Results are printed as a Markdown table and written to docs/benchmarks/vector_search.json.
"""

from __future__ import annotations

import json
import math
import os
import platform
import statistics
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DIM = 384
SIZES = (1_000, 10_000, 50_000)
K = 10
QUERIES = 30
LEGACY_QUERIES = 5  # the Python scan is slow; fewer runs keep the benchmark short
OUT = Path("docs/benchmarks/vector_search.json")


def _legacy_cosine(a: list[float], b: list[float]) -> float:
    """The v1 implementation, verbatim in behavior."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b)


def _timed(
    fn: Callable[[np.ndarray], list[int]], queries: np.ndarray
) -> tuple[float, float, list[list[int]]]:
    times, results = [], []
    for q in queries:
        start = time.perf_counter()
        results.append(fn(q))
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    p95 = times[min(len(times) - 1, math.ceil(0.95 * len(times)) - 1)]
    return statistics.median(times), p95, results


def _load(conn: psycopg.Connection, vectors: np.ndarray) -> None:
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS bench_legacy, bench_vec")
        cur.execute("CREATE TABLE bench_legacy (id int PRIMARY KEY, vector jsonb NOT NULL)")
        cur.execute(f"CREATE TABLE bench_vec (id int PRIMARY KEY, embedding vector({DIM}))")
        with cur.copy("COPY bench_legacy (id, vector) FROM STDIN") as copy:
            for i, v in enumerate(vectors):
                copy.write_row((i, json.dumps(v.tolist())))
        with cur.copy("COPY bench_vec (id, embedding) FROM STDIN WITH (FORMAT BINARY)") as copy:
            copy.set_types(["int4", "vector"])
            for i, v in enumerate(vectors):
                copy.write_row((i, v))
        cur.execute(
            "CREATE INDEX ON bench_vec USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        )
        cur.execute("ANALYZE bench_vec")
    conn.commit()


def _clustered(rng: np.random.Generator, n: int) -> np.ndarray:
    """Vectors grouped around topics, like text embeddings.

    Independent Gaussian vectors are a poor stand-in: in 384 dimensions all their pairwise
    distances are nearly equal, the "nearest" neighbors are noise and every ANN index scores
    badly on them.
    """
    centroids = rng.normal(size=(max(n // 50, 1), DIM))
    assignment = rng.integers(0, len(centroids), size=n)
    return (centroids[assignment] + 0.6 * rng.normal(size=(n, DIM))).astype(np.float32)


def _legacy(conn: psycopg.Connection, q: np.ndarray) -> list[int]:
    ql = q.tolist()
    stored = conn.execute("SELECT id, vector FROM bench_legacy").fetchall()
    scored = sorted(((_legacy_cosine(ql, v), i) for i, v in stored), reverse=True)
    return [i for _, i in scored[:K]]


def _pg(conn: psycopg.Connection, q: np.ndarray, *, exact: bool) -> list[int]:
    with conn.transaction():
        conn.execute(f"SET LOCAL enable_indexscan = {'off' if exact else 'on'}")
        conn.execute("SET LOCAL hnsw.ef_search = 100")
        found = conn.execute(
            "SELECT id FROM bench_vec ORDER BY embedding <=> %s LIMIT %s", (q, K)
        ).fetchall()
    return [r[0] for r in found]


def run() -> list[dict[str, float | int]]:
    url = os.environ["BENCH_DATABASE_URL"]
    rng = np.random.default_rng(42)
    rows: list[dict[str, float | int]] = []
    with psycopg.connect(url) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        pg_version = conn.execute("SHOW server_version").fetchone()[0]  # type: ignore[index]
        pgvector_version = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()[0]  # type: ignore[index]

        for n in SIZES:
            vectors = _clustered(rng, n)
            _load(conn, vectors)
            # Questions land near the content they ask about: a stored vector plus noise.
            picks = vectors[rng.integers(0, n, size=QUERIES)]
            queries = (picks + 0.3 * rng.normal(size=picks.shape)).astype(np.float32)
            legacy_p50, legacy_p95, _ = _timed(partial(_legacy, conn), queries[:LEGACY_QUERIES])
            exact_p50, exact_p95, exact_ids = _timed(partial(_pg, conn, exact=True), queries)
            hnsw_p50, hnsw_p95, hnsw_ids = _timed(partial(_pg, conn, exact=False), queries)
            recall = statistics.mean(
                len(set(a) & set(b)) / K for a, b in zip(exact_ids, hnsw_ids, strict=True)
            )
            row = {
                "chunks": n,
                "legacy_python_p50_ms": round(legacy_p50, 1),
                "legacy_python_p95_ms": round(legacy_p95, 1),
                "pgvector_exact_p50_ms": round(exact_p50, 2),
                "pgvector_exact_p95_ms": round(exact_p95, 2),
                "pgvector_hnsw_p50_ms": round(hnsw_p50, 2),
                "pgvector_hnsw_p95_ms": round(hnsw_p95, 2),
                "hnsw_recall_at_10": round(recall, 3),
            }
            rows.append(row)
            print(row, flush=True)

        conn.execute("DROP TABLE IF EXISTS bench_legacy, bench_vec")
        conn.commit()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "dim": DIM,
                "data": (
                    "synthetic, clustered (n/50 centroids, noise 0.6); "
                    "queries = stored vector + noise 0.3"
                ),
                "k": K,
                "hnsw": {"m": 16, "ef_construction": 64, "ef_search": 100},
                "postgres": pg_version,
                "pgvector": pgvector_version,
                "machine": platform.processor() or platform.machine(),
                "threads": os.cpu_count(),
                "os": platform.platform(terse=True),
                "results": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return rows


def markdown(rows: list[dict[str, float | int]]) -> str:
    lines = [
        "| Chunks | v1 Python scan p50 | pgvector exact p50 | pgvector HNSW p50 | HNSW recall@10 |",
        "| --: | --: | --: | --: | --: |",
    ]
    for r in rows:
        lines.append(
            f"| {r['chunks']:,} | {r['legacy_python_p50_ms']:,} ms | "
            f"{r['pgvector_exact_p50_ms']} ms | {r['pgvector_hnsw_p50_ms']} ms | "
            f"{r['hnsw_recall_at_10']:.3f} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(markdown(run()))
