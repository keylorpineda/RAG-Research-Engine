"""Retrieval benchmark: ingests the PEP corpus with the real pipeline and measures every mode.

    EVAL_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_eval \\
        uv run python -m eval.run [--rerank] [--write-baseline] [--check]

The database is wiped and rebuilt: its name must contain "eval", "test" or "bench".
Embeddings default to the local model, so no API key is needed.

Metrics (answerable questions, k = 10 candidates):
- Recall@k: share of questions with a relevant chunk in the top k.
- MRR@10: mean of 1 / rank of the first relevant chunk (0 if none in the top 10).
- nDCG@10: binary gains; ideal = every relevant chunk of the corpus ranked first.
A chunk is relevant when it belongs to the expected PEP and contains the evidence quote.

Abstention: the gate compares the best dense similarity with a threshold. The sweep reports,
per threshold, the share of answerable questions still answered (coverage) and the share of
unanswerable questions refused (abstention recall). The suggested threshold maximizes their mean.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("EMBEDDING_PROVIDER", "local")

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, settings
from app.ingestion.pipeline import ingest_document
from app.models.models import Document, DocumentStatus
from app.providers.embeddings import EmbeddingProvider, get_embedding_provider
from app.providers.llm import get_llm
from app.providers.rerank import Reranker, build_reranker
from app.retrieval.retriever import RetrievalMode, retrieve
from app.retrieval.translation import QueryTranslator
from eval.corpus import PEPS_COMMIT, fetch

ROOT = Path(__file__).parent
QUESTIONS = ROOT / "questions.jsonl"
RESULTS = ROOT / "results"
K = 10
RECALL_AT = (1, 5, 10)
REGRESSION_TOLERANCE = 0.03


@dataclass(frozen=True)
class Question:
    id: str
    lang: str
    question: str
    doc: str | None
    evidence: str | None
    answerable: bool
    hard_negative: bool = False


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def load_questions() -> list[Question]:
    lines = QUESTIONS.read_text("utf-8").splitlines()
    return [Question(**json.loads(line)) for line in lines if line.strip()]


# --- setup -----------------------------------------------------------------------------------


def database_url() -> str:
    raw = os.environ.get("EVAL_DATABASE_URL")
    if not raw:
        sys.exit("Set EVAL_DATABASE_URL to a database the benchmark may wipe.")
    url = Settings(database_url=raw).database_url
    name = make_url(url).database or ""
    if not any(tag in name for tag in ("eval", "test", "bench")):
        sys.exit(f"Refusing to wipe database {name!r}: its name must contain eval, test or bench.")
    return url


def reset_schema(url: str) -> None:
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
        conn.execute(text("DROP TYPE IF EXISTS doc_status, job_status CASCADE"))
    engine.dispose()
    config = Config(str(ROOT.parent / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")


def ingest_corpus(db: Session, embeddings: EmbeddingProvider) -> dict[str, float]:
    start = time.perf_counter()
    chunks = 0
    for path in fetch():
        doc = Document(
            filename=path.name,
            mime="text/plain",
            path=str(path),
            size=path.stat().st_size,
            status=DocumentStatus.PENDING,
        )
        db.add(doc)
        db.flush()
        chunks += ingest_document(db, doc, embeddings)
    db.commit()
    return {"chunks": chunks, "seconds": round(time.perf_counter() - start, 1)}


def relevant_chunk_ids(db: Session, question: Question) -> set[int]:
    assert question.evidence
    assert question.doc
    needle = normalize(question.evidence)
    rows = db.execute(
        text(
            "SELECT c.id, c.text FROM doc_chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE d.filename = :doc"
        ),
        {"doc": question.doc},
    ).all()
    return {chunk_id for chunk_id, body in rows if needle in normalize(body)}


# --- metrics ---------------------------------------------------------------------------------


def ranking_metrics(
    ranked_ids: list[int], relevant: set[int], ranked_docs: list[str], doc: str
) -> dict[str, float]:
    first = next((i for i, cid in enumerate(ranked_ids, 1) if cid in relevant), None)
    dcg = sum(1 / math.log2(i + 1) for i, cid in enumerate(ranked_ids[:K], 1) if cid in relevant)
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(relevant), K) + 1))
    metrics = {f"recall@{k}": float(first is not None and first <= k) for k in RECALL_AT}
    metrics["mrr@10"] = 1 / first if first is not None and first <= K else 0.0
    metrics["ndcg@10"] = dcg / ideal if ideal else 0.0
    metrics["doc_recall@5"] = float(doc in ranked_docs[:5])
    return metrics


def mean_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
    return {key: round(statistics.mean(r[key] for r in rows), 3) for key in rows[0]}


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, math.ceil(p * len(ordered)) - 1))]


def evaluate_mode(
    db: Session,
    questions: list[Question],
    *,
    relevant: dict[str, set[int]],
    mode: RetrievalMode,
    embeddings: EmbeddingProvider,
    reranker: Reranker | None,
    translator: QueryTranslator | None = None,
) -> dict[str, Any]:
    per_question: dict[str, dict[str, float]] = {}
    latencies: list[float] = []
    for q in questions:
        start = time.perf_counter()
        lexical_query = translator.for_lexical(q.question) if translator else None
        result = retrieve(
            db,
            q.question,
            mode=mode,
            k=K,
            embeddings=embeddings,
            reranker=reranker,
            lexical_query=lexical_query,
        )
        latencies.append((time.perf_counter() - start) * 1000)
        assert q.doc
        per_question[q.id] = ranking_metrics(
            [c.hit.chunk_id for c in result.candidates],
            relevant[q.id],
            [c.hit.filename for c in result.candidates],
            q.doc,
        )

    by_lang = {
        lang: mean_metrics([per_question[q.id] for q in questions if q.lang == lang])
        for lang in sorted({q.lang for q in questions})
    }
    return {
        "all": mean_metrics(list(per_question.values())),
        "by_lang": by_lang,
        "latency_ms": {
            "p50": round(statistics.median(latencies), 1),
            "p95": round(percentile(latencies, 0.95), 1),
        },
        "misses_at_10": sorted(q for q, m in per_question.items() if m["recall@10"] == 0),
    }


def abstention_sweep(
    db: Session, questions: list[Question], embeddings: EmbeddingProvider
) -> dict[str, Any]:
    best: dict[str, float] = {}
    for q in questions:
        result = retrieve(db, q.question, mode=RetrievalMode.DENSE, k=1, embeddings=embeddings)
        best[q.id] = result.best_dense_score if result.best_dense_score is not None else -1.0

    answerable = [q for q in questions if q.answerable]
    unanswerable = [q for q in questions if not q.answerable]
    hard = [q for q in unanswerable if q.hard_negative]

    def rates(threshold: float) -> dict[str, float]:
        coverage = statistics.mean(best[q.id] >= threshold for q in answerable)
        refused = statistics.mean(best[q.id] < threshold for q in unanswerable)
        refused_hard = statistics.mean(best[q.id] < threshold for q in hard) if hard else 0.0
        abstained = [q for q in questions if best[q.id] < threshold]
        precision = statistics.mean(not q.answerable for q in abstained) if abstained else 1.0
        return {
            "threshold": round(threshold, 2),
            "answerable_coverage": round(coverage, 3),
            "abstention_recall": round(refused, 3),
            "abstention_recall_hard": round(refused_hard, 3),
            "abstention_precision": round(precision, 3),
            "balanced_accuracy": round((coverage + refused) / 2, 3),
        }

    sweep = [rates(t / 100) for t in range(0, 101)]
    chosen = max(sweep, key=lambda r: (r["balanced_accuracy"], r["answerable_coverage"]))
    return {
        "suggested": chosen,
        "at_configured": rates(settings.abstain_threshold),
        "configured_threshold": settings.abstain_threshold,
        "sweep": [rates(t / 100) for t in range(20, 75, 5)],
        "best_similarity": {
            "answerable_median": round(statistics.median(best[q.id] for q in answerable), 3),
            "unanswerable_median": round(statistics.median(best[q.id] for q in unanswerable), 3),
        },
    }


# --- report ----------------------------------------------------------------------------------


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "| Mode | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Doc recall@5 "
        "| Recall@5 EN | Recall@5 ES | p50 |",
        "| :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: |",
    ]
    for mode, r in report["modes"].items():
        a, en, es = r["all"], r["by_lang"].get("en", {}), r["by_lang"].get("es", {})
        lines.append(
            f"| {mode} | {a['recall@1']:.3f} | {a['recall@5']:.3f} | {a['recall@10']:.3f} | "
            f"{a['mrr@10']:.3f} | {a['ndcg@10']:.3f} | {a['doc_recall@5']:.3f} | "
            f"{en.get('recall@5', 0):.3f} | "
            f"{es.get('recall@5', 0):.3f} | {r['latency_ms']['p50']} ms |"
        )
    ab = report["abstention"]
    lines += [
        "",
        "| Threshold | Answerable answered | Unanswerable refused | Hard negatives refused | "
        "Abstention precision |",
        "| --: | --: | --: | --: | --: |",
    ]
    for r in ab["sweep"]:
        lines.append(
            f"| {r['threshold']:.2f} | {r['answerable_coverage']:.3f} | "
            f"{r['abstention_recall']:.3f} | {r['abstention_recall_hard']:.3f} | "
            f"{r['abstention_precision']:.3f} |"
        )
    s = ab["suggested"]
    lines.append(
        f"\nSuggested threshold: **{s['threshold']:.2f}** (balanced accuracy "
        f"{s['balanced_accuracy']:.3f}). Configured: {ab['configured_threshold']:.2f}."
    )
    return "\n".join(lines)


def check_regression(report: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    failures = []
    for mode in ("hybrid", "dense"):
        now = report["modes"][mode]["all"]["recall@5"]
        before = baseline["modes"][mode]["all"]["recall@5"]
        if now < before - REGRESSION_TOLERANCE:
            failures.append(f"{mode} recall@5 dropped from {before:.3f} to {now:.3f}")
    now_ba = report["abstention"]["at_configured"]["balanced_accuracy"]
    before_ba = baseline["abstention"]["at_configured"]["balanced_accuracy"]
    if now_ba < before_ba - REGRESSION_TOLERANCE:
        failures.append(f"abstention balanced accuracy dropped from {before_ba} to {now_ba}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--rerank", action="store_true", help="also run hybrid + Cohere rerank")
    parser.add_argument(
        "--translate",
        action="store_true",
        help="also run lexical and hybrid with translated questions (needs the LLM)",
    )
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--check", action="store_true", help="fail on regression vs baseline")
    parser.add_argument("--tag", help="also save the report as results/<tag>.json")
    args = parser.parse_args()

    url = database_url()
    reset_schema(url)
    embeddings = get_embedding_provider()
    questions = load_questions()
    answerable = [q for q in questions if q.answerable]

    with sessionmaker(bind=create_engine(url))() as db:
        ingestion = ingest_corpus(db, embeddings)
        relevant = {q.id: relevant_chunk_ids(db, q) for q in answerable}
        if missing := [q.id for q in answerable if not relevant[q.id]]:
            sys.exit(f"Evidence not found in any chunk for {missing}; shorten those quotes.")

        modes: dict[str, Any] = {}
        for mode in (RetrievalMode.DENSE, RetrievalMode.LEXICAL, RetrievalMode.HYBRID):
            modes[mode.value] = evaluate_mode(
                db, answerable, relevant=relevant, mode=mode, embeddings=embeddings, reranker=None
            )
            print(f"{mode.value}: {modes[mode.value]['all']}", flush=True)
        if args.rerank:
            reranker = build_reranker(Settings(rerank_provider="cohere"))
            modes["hybrid+rerank"] = evaluate_mode(
                db,
                answerable,
                relevant=relevant,
                mode=RetrievalMode.HYBRID,
                embeddings=embeddings,
                reranker=reranker,
            )
        if args.translate:
            translator = QueryTranslator(get_llm)
            for mode in (RetrievalMode.LEXICAL, RetrievalMode.HYBRID):
                # Latency includes the translation, a model call per new question (then cached).
                modes[f"{mode.value}+translation"] = evaluate_mode(
                    db,
                    answerable,
                    relevant=relevant,
                    mode=mode,
                    embeddings=embeddings,
                    reranker=None,
                    translator=translator,
                )
                print(f"{mode.value}+translation: {modes[f'{mode.value}+translation']['all']}")
        abstention = abstention_sweep(db, questions, embeddings)

    report = {
        "corpus": {"peps_commit": PEPS_COMMIT, "documents": 26, **ingestion},
        "questions": {
            "answerable": len(answerable),
            "unanswerable": len(questions) - len(answerable),
            "by_lang": {lang: sum(q.lang == lang for q in answerable) for lang in ("en", "es")},
        },
        "config": {
            "embedding_model": embeddings.name,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "k": K,
            "hnsw_ef_search": 100,
        },
        "modes": modes,
        "abstention": abstention,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    table = markdown(report)
    (RESULTS / "latest.md").write_text(table + "\n", "utf-8")
    print(table)
    if args.tag:
        (RESULTS / f"{args.tag}.json").write_text(json.dumps(report, indent=2), "utf-8")

    baseline_path = RESULTS / "baseline.json"
    if args.write_baseline:
        baseline_path.write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    if args.check:
        failures = check_regression(report, json.loads(baseline_path.read_text("utf-8")))
        for failure in failures:
            print(f"REGRESSION: {failure}")
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
