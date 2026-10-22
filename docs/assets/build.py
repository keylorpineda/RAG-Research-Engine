"""Generates the README illustrations, in light and dark variants.

    uv run python docs/assets/build.py

Diagrams are drawn from the code's real stages; charts read the committed benchmark results
(eval/results/baseline.json and docs/benchmarks/vector_search.json), so they cannot drift from
the numbers in docs/BENCHMARKS.md. Every animation stops under prefers-reduced-motion.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

PALETTES = {
    "light": {
        "bg": "#FFFFFF",
        "surface": "#F3F7F6",
        "border": "#D9E4E2",
        "text": "#0E1D1C",
        "muted": "#55676A",
        "accent": "#0D9488",
        "accent2": "#2563EB",
        "soft": "#E3F4F1",
        "soft2": "#E6EEFD",
        "warn": "#C2410C",
        "warnsoft": "#FDEEE4",
        "grid": "#E7EEED",
    },
    "dark": {
        "bg": "#0D1117",
        "surface": "#151B23",
        "border": "#2D3742",
        "text": "#E6EDF3",
        "muted": "#8B98A5",
        "accent": "#2DD4BF",
        "accent2": "#60A5FA",
        "soft": "#0E2A28",
        "soft2": "#132239",
        "warn": "#FB923C",
        "warnsoft": "#2C1A0E",
        "grid": "#1D252F",
    },
}

FONT = "'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def svg(width: int, height: int, label: str, style: str, body: str, p: dict[str, str]) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{label}">\n'
        f"<style>\n  text{{font-family:{FONT};fill:{p['text']}}}\n"
        f"  .mono{{font-family:{MONO}}}\n  .muted{{fill:{p['muted']}}}\n{style}\n"
        "  @media (prefers-reduced-motion:reduce){*{animation:none!important}"
        ".traveler{display:none}}\n</style>\n"
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="20" '
        f'fill="{p["bg"]}" stroke="{p["border"]}"/>\n{body}\n</svg>\n'
    )


# --- hero ------------------------------------------------------------------------------------


def hero(p: dict[str, str]) -> str:
    style = f"""
  .doc{{fill:{p["surface"]};stroke:{p["border"]};stroke-width:1.5}}
  .line{{fill:{p["border"]}}}
  .hit{{fill:{p["soft"]};stroke:{p["accent"]};stroke-width:2;opacity:0;animation:hit 6s infinite}}
  .badge{{opacity:0;animation:hit 6s infinite}}
  .h2{{animation-delay:.4s}} .h3{{animation-delay:.8s}}
  @keyframes hit{{0%,30%{{opacity:0}}40%,85%{{opacity:1}}100%{{opacity:0}}}}
  .scan{{animation:scan 6s infinite}}
  @keyframes scan{{0%{{transform:translateY(0);opacity:0}}5%{{opacity:.9}}35%{{transform:translateY(150px);opacity:.9}}40%,100%{{opacity:0;transform:translateY(150px)}}}}
"""
    docs = []
    for i, x in enumerate((690, 800, 910, 1020)):
        lines = "".join(
            f'<rect class="line" x="{x + 14}" y="{86 + j * 16}" width="{70 - (j * 13 + i * 7) % 30}" height="5" rx="2.5"/>'
            for j in range(9)
        )
        docs.append(f'<rect class="doc" x="{x}" y="70" width="96" height="164" rx="10"/>{lines}')
    hits = ""
    for n, (x, y, cls) in enumerate(((800, 118, "h1"), (1020, 166, "h2"), (690, 198, "h3")), 1):
        hits += (
            f'<rect class="hit {cls}" x="{x + 6}" y="{y}" width="84" height="24" rx="6"/>'
            f'<g class="badge {cls}"><circle cx="{x + 92}" cy="{y}" r="12" fill="{p["accent"]}"/>'
            f'<text x="{x + 92}" y="{y + 4.5}" text-anchor="middle" font-size="12" font-weight="700" '
            f'fill="{p["bg"]}" style="fill:{p["bg"]}">{n}</text></g>'
        )
    scan = (
        f'<rect class="scan" x="676" y="70" width="452" height="3" rx="1.5" fill="{p["accent"]}"/>'
    )
    body = f"""
<text x="64" y="118" font-size="44" font-weight="800">RAG Research Engine</text>
<text x="66" y="160" font-size="20" class="muted">Answers from your documents, with sources you can check,</text>
<text x="66" y="188" font-size="20" class="muted">and a clear “I don't know” when the evidence is not there.</text>
<g font-size="14" font-weight="600">
  <rect x="66" y="218" width="150" height="32" rx="16" fill="{p["soft"]}"/><text x="141" y="239" text-anchor="middle" style="fill:{p["accent"]}">pgvector + HNSW</text>
  <rect x="226" y="218" width="130" height="32" rx="16" fill="{p["soft2"]}"/><text x="291" y="239" text-anchor="middle" style="fill:{p["accent2"]}">hybrid · RRF</text>
  <rect x="366" y="218" width="170" height="32" rx="16" fill="{p["warnsoft"]}"/><text x="451" y="239" text-anchor="middle" style="fill:{p["warn"]}">abstains, measured</text>
</g>
{"".join(docs)}{hits}{scan}
"""
    return svg(1200, 300, "RAG Research Engine", style, body, p)


# --- flow diagrams ---------------------------------------------------------------------------


def node(x: float, y: float, w: float, h: float, title: str, sub: str, p: dict[str, str],
         kind: str = "n", index: int = 0) -> str:  # fmt: skip
    fill, stroke = (p["surface"], p["border"]) if kind == "n" else (p["warnsoft"], p["warn"])
    return (
        f'<g class="node k{index}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" text-anchor="middle" font-size="16" '
        f'font-weight="700">{title}</text>'
        f'<text x="{x + w / 2}" y="{y + h / 2 + 18}" text-anchor="middle" font-size="12.5" '
        f'class="muted">{sub}</text></g>'
    )


def pulse_style(p: dict[str, str], count: int, period: float) -> str:
    rules = []
    for i in range(count):
        start = i / count * 100
        end = start + 100 / count
        rules.append(
            f".k{i} rect{{animation:k{i} {period}s linear infinite}}"
            f"@keyframes k{i}{{0%,{start:.1f}%{{stroke:{p['border']}}}"
            f"{start + 0.1:.1f}%,{end - 0.1:.1f}%{{stroke:{p['accent']}}}"
            f"{end:.1f}%,100%{{stroke:{p['border']}}}}}"
        )
    return "\n".join(rules)


def ingest(p: dict[str, str]) -> str:
    stages = [
        ("Upload", "safe names · size limit"),
        ("Queue", "jobs · SKIP LOCKED"),
        ("Chunk", "1,000 chars · overlap"),
        ("Embed", "Cohere or local ONNX"),
        ("Postgres", "vector · tsvector"),
    ]
    w, gap, y, h = 196, 40, 96, 92
    x0 = (1200 - (len(stages) * w + (len(stages) - 1) * gap)) / 2
    nodes = "".join(
        node(x0 + i * (w + gap), y, w, h, t, s, p, index=i) for i, (t, s) in enumerate(stages)
    )
    path = f"M{x0 + w / 2} {y + h + 34}H{x0 + 4 * (w + gap) + w / 2}"
    style = f"""
  .flow{{stroke-dasharray:6 10;animation:dash 1s linear infinite}}
  @keyframes dash{{to{{stroke-dashoffset:-16}}}}
{pulse_style(p, len(stages), 7.5)}
"""
    body = f"""
<text x="40" y="52" font-size="18" font-weight="800">Ingestion</text>
<text x="140" y="52" font-size="14" class="muted">runs in a worker process; any number of workers share the queue</text>
{nodes}
<path d="{path}" stroke="{p["border"]}" stroke-width="2"/>
<path class="flow" d="{path}" stroke="{p["accent"]}" stroke-width="2" opacity=".7"/>
<circle class="traveler" r="6" fill="{p["accent"]}"><animateMotion dur="7.5s" repeatCount="indefinite" path="{path}"/></circle>
<text x="600" y="{y + h + 64}" text-anchor="middle" font-size="12.5" class="muted">expired leases are reclaimed · failures retry with backoff · re-ingest replaces chunks</text>
"""
    return svg(1200, 290, "Ingestion pipeline", style, body, p)


def query(p: dict[str, str]) -> str:
    style = """
  .flow{stroke-dasharray:6 10;animation:dash 1s linear infinite}
  @keyframes dash{to{stroke-dashoffset:-16}}
  .gate{animation:gate 3s ease-in-out infinite;transform-origin:735px 175px}
  @keyframes gate{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
"""
    a, b = p["accent"], p["accent2"]
    edges = [
        ("M210 175C250 175 250 110 290 110", a),
        ("M210 175C250 175 250 240 290 240", b),
        ("M470 110C510 110 510 175 545 175", a),
        ("M470 240C510 240 510 175 545 175", b),
        ("M655 175H675", a),
        ("M795 175H880", a),
        ("M735 235V300", p["warn"]),
    ]
    paths = "".join(
        f'<path d="{d}" stroke="{p["border"]}" stroke-width="2" fill="none"/>'
        f'<path class="flow" d="{d}" stroke="{c}" stroke-width="2" fill="none" opacity=".75"/>'
        for d, c in edges
    )
    travel = "M210 175C250 175 250 110 290 110H470C510 110 510 175 545 175H655M675 175H795H880"
    body = f"""
<text x="40" y="52" font-size="18" font-weight="800">Question answering</text>
<text x="225" y="52" font-size="14" class="muted">the gate decides before the language model is called</text>
{paths}
<circle class="traveler" r="6" fill="{a}"><animateMotion dur="6s" repeatCount="indefinite" path="{travel}"/></circle>
{node(40, 135, 170, 80, "Question", "EN or ES", p)}
{node(290, 75, 180, 70, "Dense", "pgvector HNSW", p)}
{node(290, 205, 180, 70, "Lexical", "Postgres full-text", p)}
{node(545, 135, 110, 80, "RRF", "fuse ranks", p)}
<g class="gate"><path d="M735 115L795 175L735 235L675 175Z" fill="{p["soft"]}" stroke="{a}" stroke-width="2"/>
<text x="735" y="172" text-anchor="middle" font-size="13" font-weight="700">best cos</text>
<text x="735" y="190" text-anchor="middle" font-size="13" font-weight="700">≥ τ ?</text></g>
{node(880, 120, 280, 110, "Answer with [n]", "temperature 0 · citations checked", p)}
{node(620, 300, 230, 70, "Abstain", "insufficient_evidence", p, kind="w")}
<text x="820" y="164" font-size="12" class="muted">yes</text>
<text x="745" y="275" font-size="12" class="muted">no</text>
<text x="1020" y="262" text-anchor="middle" font-size="12.5" class="muted">invented [n] are removed and reported</text>
<text x="1020" y="282" text-anchor="middle" font-size="12.5" class="muted">"NO_ANSWER" → model_declined</text>
"""
    return svg(1200, 400, "Query pipeline with the abstention gate", style, body, p)


# --- charts ----------------------------------------------------------------------------------


def recall_chart(p: dict[str, str], report: dict) -> str:
    modes = [("dense", "Dense"), ("lexical", "Lexical"), ("hybrid", "Hybrid (RRF)")]
    series = [("all", "All questions", p["accent"]), ("en", "English", p["accent2"]),
              ("es", "Spanish", p["warn"])]  # fmt: skip
    left, top, plot_h, group_w = 110, 90, 210, 330
    bar_w = 70
    bars, labels = [], []
    for g, (key, name) in enumerate(modes):
        data = report["modes"][key]
        values = [data["all"]["recall@5"], data["by_lang"]["en"]["recall@5"],
                  data["by_lang"]["es"]["recall@5"]]  # fmt: skip
        gx = left + 20 + g * group_w
        for s, (value, (_, _, color)) in enumerate(zip(values, series, strict=True)):
            h = value * plot_h
            x = gx + s * (bar_w + 14)
            y = top + plot_h - h
            delay = g * 0.25 + s * 0.08
            bars.append(
                f'<rect class="bar" style="animation-delay:{delay:.2f}s" x="{x}" y="{y:.1f}" '
                f'width="{bar_w}" height="{h:.1f}" rx="6" fill="{color}"/>'
                f'<text x="{x + bar_w / 2}" y="{y - 8:.1f}" text-anchor="middle" font-size="14" '
                f'font-weight="700">{value:.2f}</text>'
            )
        labels.append(
            f'<text x="{gx + (3 * bar_w + 28) / 2}" y="{top + plot_h + 30}" text-anchor="middle" '
            f'font-size="16" font-weight="700">{name}</text>'
        )
    grid = "".join(
        f'<line x1="{left}" x2="1150" y1="{top + plot_h - v * plot_h}" y2="{top + plot_h - v * plot_h}" '
        f'stroke="{p["grid"]}"/><text x="{left - 12}" y="{top + plot_h - v * plot_h + 5}" '
        f'text-anchor="end" font-size="12" class="muted">{v:.2f}</text>'
        for v in (0, 0.25, 0.5, 0.75, 1.0)
    )
    legend = "".join(
        f'<rect x="{700 + i * 150}" y="38" width="14" height="14" rx="3" fill="{c}"/>'
        f'<text x="{720 + i * 150}" y="50" font-size="14">{n}</text>'
        for i, (_, n, c) in enumerate(series)
    )
    style = """
  .bar{transform-box:fill-box;transform-origin:bottom;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}
  @keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
"""
    q = report["questions"]
    body = f"""
<text x="40" y="52" font-size="18" font-weight="800">Recall@5 by retrieval mode</text>
{legend}{grid}{"".join(bars)}{"".join(labels)}
<text x="40" y="372" font-size="12.5" class="muted">{q["answerable"]} questions ({q["by_lang"]["en"]} EN, {q["by_lang"]["es"]} ES) over 26 PEPs · {report["config"]["embedding_model"].split("/")[-1]} · a hit = chunk containing the evidence quote</text>
"""
    return svg(1200, 390, "Recall at 5 by retrieval mode", style, body, p)


def latency_chart(p: dict[str, str], vector: dict) -> str:
    row = vector["results"][-1]
    items = [
        ("v1 · Python loop over JSON", row["legacy_python_p50_ms"], p["warn"]),
        ("pgvector · exact scan", row["pgvector_exact_p50_ms"], p["accent2"]),
        ("pgvector · HNSW", row["pgvector_hnsw_p50_ms"], p["accent"]),
    ]
    left, width = 300, 760
    lo, hi = math.log10(1), math.log10(100_000)

    def scale(ms: float) -> float:
        return (math.log10(max(ms, 1)) - lo) / (hi - lo) * width

    bars = []
    for i, (name, ms, color) in enumerate(items):
        y = 96 + i * 52
        w = scale(ms)
        text = f"{ms / 1000:,.1f} s" if ms >= 1000 else f"{ms:,.1f} ms"
        bars.append(
            f'<text x="{left - 16}" y="{y + 22}" text-anchor="end" font-size="15" font-weight="600">{name}</text>'
            f'<rect class="hbar" style="animation-delay:{i * 0.2:.1f}s" x="{left}" y="{y}" width="{w:.1f}" '
            f'height="32" rx="6" fill="{color}"/>'
            f'<text x="{left + w + 10:.1f}" y="{y + 22}" font-size="15" font-weight="700">{text}</text>'
        )
    ticks = "".join(
        f'<line x1="{left + scale(t):.1f}" x2="{left + scale(t):.1f}" y1="86" y2="250" stroke="{p["grid"]}"/>'
        f'<text x="{left + scale(t):.1f}" y="270" text-anchor="middle" font-size="12" class="muted">{label}</text>'
        for t, label in (
            (1, "1 ms"),
            (10, "10 ms"),
            (100, "100 ms"),
            (1000, "1 s"),
            (10000, "10 s"),
            (100000, "100 s"),
        )
    )
    style = """
  .hbar{transform-box:fill-box;transform-origin:left;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}
  @keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
"""
    speedup = row["legacy_python_p50_ms"] / row["pgvector_hnsw_p50_ms"]
    body = f"""
<text x="40" y="52" font-size="18" font-weight="800">Top-10 search over {row["chunks"]:,} chunks</text>
<text x="1160" y="52" text-anchor="end" font-size="15" font-weight="700" style="fill:{p["accent"]}">{speedup:,.0f}× faster · recall@10 {row["hnsw_recall_at_10"]:.2f}</text>
{ticks}{"".join(bars)}
<text x="40" y="300" font-size="12.5" class="muted">median latency, log scale · 384-dim vectors · Postgres {vector["postgres"]}, pgvector {vector["pgvector"]} · bench/vector_search.py</text>
"""
    return svg(1200, 320, "Vector search latency", style, body, p)


def abstention_chart(p: dict[str, str], report: dict) -> str:
    ab = report["abstention"]
    sweep = ab["full_sweep"] if "full_sweep" in ab else ab["sweep"]
    left, top, w, h = 110, 80, 840, 220

    def px(t: float) -> float:
        return left + (t - 0.2) / 0.5 * w

    def py(v: float) -> float:
        return top + h - v * h

    pts = [r for r in sweep if 0.2 <= r["threshold"] <= 0.7]
    cov = " ".join(f"{px(r['threshold']):.1f},{py(r['answerable_coverage']):.1f}" for r in pts)
    rec = " ".join(f"{px(r['threshold']):.1f},{py(r['abstention_recall']):.1f}" for r in pts)
    t = ab["configured_threshold"]
    at = ab["at_configured"]
    grid = "".join(
        f'<line x1="{left}" x2="{left + w}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{p["grid"]}"/>'
        f'<text x="{left - 12}" y="{py(v) + 5:.1f}" text-anchor="end" font-size="12" class="muted">{v:.0%}</text>'
        for v in (0, 0.25, 0.5, 0.75, 1)
    ) + "".join(
        f'<text x="{px(x):.1f}" y="{top + h + 24}" text-anchor="middle" font-size="12" class="muted">{x:.1f}</text>'
        for x in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
    )
    style = """
  .ln{fill:none;stroke-width:3;stroke-linejoin:round;stroke-dasharray:2000;stroke-dashoffset:2000;animation:draw 2.4s ease-out forwards}
  .l2{animation-delay:.4s}
  @keyframes draw{to{stroke-dashoffset:0}}
  .mark{opacity:0;animation:show .6s 2.2s forwards}
  @keyframes show{to{opacity:1}}
"""
    body = f"""
<text x="40" y="52" font-size="18" font-weight="800">Where to abstain</text>
<text x="210" y="52" font-size="14" class="muted">best dense similarity threshold τ</text>
<rect x="760" y="36" width="14" height="14" rx="3" fill="{p["accent"]}"/><text x="780" y="48" font-size="14">answerable questions answered</text>
<rect x="760" y="58" width="14" height="14" rx="3" fill="{p["warn"]}"/><text x="780" y="70" font-size="14">unanswerable questions refused</text>
{grid}
<polyline class="ln" points="{cov}" stroke="{p["accent"]}"/>
<polyline class="ln l2" points="{rec}" stroke="{p["warn"]}"/>
<g class="mark"><line x1="{px(t):.1f}" x2="{px(t):.1f}" y1="{top - 6}" y2="{top + h}" stroke="{p["text"]}" stroke-dasharray="4 4"/>
<text x="{px(t) - 10:.1f}" y="{top + h - 14}" text-anchor="end" font-size="14" font-weight="700">τ = {t:.2f}: {at["answerable_coverage"]:.0%} answered · {at["abstention_recall"]:.0%} refused</text></g>
<text x="40" y="350" font-size="12.5" class="muted">{report["questions"]["unanswerable"]} unanswerable questions, 6 of them about Python topics the corpus does not cover · calibrated on this set (eval/run.py)</text>
"""
    return svg(1200, 370, "Abstention threshold trade-off", style, body, p)


def main() -> None:
    report = json.loads((ROOT / "eval/results/baseline.json").read_text("utf-8"))
    vector = json.loads((ROOT / "docs/benchmarks/vector_search.json").read_text("utf-8"))
    for theme, palette in PALETTES.items():
        files = {
            "hero": hero(palette),
            "ingest": ingest(palette),
            "query": query(palette),
            "recall": recall_chart(palette, report),
            "latency": latency_chart(palette, vector),
            "abstention": abstention_chart(palette, report),
        }
        for name, content in files.items():
            (OUT / f"{name}-{theme}.svg").write_text(content, "utf-8", newline="\n")
    print(f"wrote {len(files) * len(PALETTES)} SVGs to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
