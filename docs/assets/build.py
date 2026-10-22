"""Generates the README cards (hero, results, how it works) in light and dark variants.

    uv run python docs/assets/build.py

All three cards share one frame, width and palette (*Deep Ink*, the web app's design system),
so the README reads as one piece. The results card reads the committed result files, so it
cannot drift from docs/BENCHMARKS.md. Every animation stops under prefers-reduced-motion.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
W = 1200

PALETTES = {
    "light": {
        "card": "#FFFFFF", "border": "#E3E8EE", "panel": "#F6F8FA", "text": "#131922",
        "muted": "#556170", "faint": "#5F6B79", "track": "#E6EAEF", "accent": "#2E7564",
        "accent_soft": "#E1F1EC", "accent_fg": "#1F5A4C", "dense": "#5068BF", "lex": "#8A5FBF",
        "rose": "#B5566E", "rose_soft": "#F8E7EC", "line": "#D9DFE6", "on_accent": "#FFFFFF",
    },
    "dark": {
        "card": "#12161D", "border": "#262E3A", "panel": "#0E1218", "text": "#E7EBF0",
        "muted": "#9AA5B3", "faint": "#8591A0", "track": "#1F2630", "accent": "#8CC7B5",
        "accent_soft": "#1F3A34", "accent_fg": "#B4DDD0", "dense": "#A3B4EC", "lex": "#C4A9E3",
        "rose": "#DDA6B3", "rose_soft": "#2E1F27", "line": "#262E3A", "on_accent": "#0B0E13",
    },
}  # fmt: skip

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def card(height: int, label: str, style: str, body: str, p: dict[str, str]) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" '
        f'height="{height}" role="img" aria-label="{label}">\n<style>\n'
        f"  text{{font-family:{SANS};fill:{p['text']}}}\n"
        f"  .mono{{font-family:{MONO}}}\n  .muted{{fill:{p['muted']}}}\n  .faint{{fill:{p['faint']}}}\n"
        f"  .h{{font-weight:700;letter-spacing:-.01em}}\n{style}\n"
        "  @media (prefers-reduced-motion:reduce){*{animation:none!important}.traveler{display:none}}\n"
        "</style>\n"
        f'<rect x=".5" y=".5" width="{W - 1}" height="{height - 1}" rx="24" '
        f'fill="{p["card"]}" stroke="{p["border"]}"/>\n{body}\n</svg>\n'
    )


def logo(x: float, y: float, size: float, p: dict[str, str]) -> str:
    s = size / 28
    return (
        f'<g transform="translate({x} {y}) scale({s:.3f})">'
        f'<path d="M10 5H6v18h4" fill="none" stroke="{p["accent"]}" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M18 5h4v18h-4" fill="none" stroke="{p["accent"]}" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle class="blink" cx="14" cy="14" r="2.4" fill="{p["text"]}"/></g>'
    )


def header(title: str, subtitle: str, p: dict[str, str]) -> str:
    return (
        f"{logo(40, 30, 26, p)}"
        f'<text x="76" y="50" font-size="20" class="h">{title}</text>'
        f'<text x="{W - 40}" y="50" font-size="13" class="mono faint" text-anchor="end">{subtitle}</text>'
        f'<line x1="40" y1="76" x2="{W - 40}" y2="76" stroke="{p["border"]}"/>'
    )


# --- hero ------------------------------------------------------------------------------------


def hero(p: dict[str, str]) -> str:
    style = f"""
  .blink{{animation:blink 2.8s ease-in-out infinite}}
  @keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
  .c1 rect,.c2 rect,.c3 rect{{animation-duration:7.5s;animation-iteration-count:infinite}}
  .c1 rect{{animation-name:on1}}.c2 rect{{animation-name:on2}}.c3 rect{{animation-name:on3}}
  .c1 text,.c2 text,.c3 text{{animation-duration:7.5s;animation-iteration-count:infinite}}
  .c1 text{{animation-name:t1}}.c2 text{{animation-name:t2}}.c3 text{{animation-name:t3}}
  .s1,.s2,.s3{{animation-duration:7.5s;animation-iteration-count:infinite}}
  .s1{{animation-name:b1}}.s2{{animation-name:b2}}.s3{{animation-name:b3}}
  @keyframes on1{{0%,4%,30%,100%{{fill:{p["accent_soft"]}}}8%,26%{{fill:{p["accent"]}}}}}
  @keyframes on2{{0%,37%,63%,100%{{fill:{p["accent_soft"]}}}41%,59%{{fill:{p["accent"]}}}}}
  @keyframes on3{{0%,70%,96%,100%{{fill:{p["accent_soft"]}}}74%,92%{{fill:{p["accent"]}}}}}
  @keyframes t1{{0%,4%,30%,100%{{fill:{p["accent_fg"]}}}8%,26%{{fill:{p["on_accent"]}}}}}
  @keyframes t2{{0%,37%,63%,100%{{fill:{p["accent_fg"]}}}41%,59%{{fill:{p["on_accent"]}}}}}
  @keyframes t3{{0%,70%,96%,100%{{fill:{p["accent_fg"]}}}74%,92%{{fill:{p["on_accent"]}}}}}
  @keyframes b1{{0%,4%,30%,100%{{stroke:{p["border"]}}}8%,26%{{stroke:{p["accent"]}}}}}
  @keyframes b2{{0%,37%,63%,100%{{stroke:{p["border"]}}}41%,59%{{stroke:{p["accent"]}}}}}
  @keyframes b3{{0%,70%,96%,100%{{stroke:{p["border"]}}}74%,92%{{stroke:{p["accent"]}}}}}
  .rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
  .r2{{animation-delay:.12s}}.r3{{animation-delay:.24s}}
  @keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
"""

    def chip(cls: str, x: float, y: float, n: int) -> str:
        return (
            f'<g class="{cls}"><rect x="{x}" y="{y}" width="22" height="22" rx="6" '
            f'fill="{p["accent_soft"]}"/><text x="{x + 11}" y="{y + 15.5}" font-size="12" '
            f'class="mono" text-anchor="middle" fill="{p["accent_fg"]}">{n}</text></g>'
        )

    def bar(x: float, y: float, w: float) -> str:
        return f'<rect x="{x}" y="{y}" width="{w}" height="9" rx="4.5" fill="{p["track"]}"/>'

    px, py = 676, 46
    answer = (
        f'<rect x="{px}" y="{py}" width="484" height="262" rx="16" fill="{p["panel"]}" stroke="{p["border"]}"/>'
        f'<text x="{px + 22}" y="{py + 32}" font-size="13" class="muted">How are coroutines declared?</text>'
        f"{bar(px + 22, py + 52, 210)}{chip('c1', px + 238, py + 45, 1)}{bar(px + 268, py + 52, 160)}"
        f"{bar(px + 22, py + 76, 120)}{chip('c2', px + 148, py + 69, 2)}{bar(px + 178, py + 76, 220)}"
        f"{bar(px + 22, py + 100, 260)}{chip('c3', px + 288, py + 93, 3)}"
    )
    sources = ""
    for i, (w1, w2) in enumerate(((300, 210), (270, 240), (320, 180))):
        y = py + 128 + i * 42
        sources += (
            f'<rect class="s{i + 1}" x="{px + 22}" y="{y}" width="440" height="34" rx="9" '
            f'fill="{p["card"]}" stroke="{p["border"]}"/>'
            f'<text x="{px + 38}" y="{y + 22}" font-size="11.5" class="mono muted">{i + 1}</text>'
            f'<text x="{px + 58}" y="{y + 22}" font-size="11.5" class="mono">pep-0492.rst</text>'
            f'<rect x="{px + 168}" y="{y + 13}" width="{w1 * 0.55:.0f}" height="7" rx="3.5" fill="{p["track"]}"/>'
            f'<rect x="{px + 168 + w1 * 0.55 + 10:.0f}" y="{y + 13}" width="{w2 * 0.3:.0f}" height="7" rx="3.5" fill="{p["track"]}"/>'
        )

    def pill(x: float, text: str, fill: str, color: str, width: float) -> str:
        return (
            f'<rect x="{x}" y="262" width="{width}" height="32" rx="16" fill="{fill}"/>'
            f'<text x="{x + width / 2}" y="283" font-size="13.5" font-weight="600" '
            f'text-anchor="middle" fill="{color}">{text}</text>'
        )

    body = f"""
<g class="rise">{logo(56, 58, 48, p)}</g>
<text class="rise r2 h" x="56" y="168" font-size="50">Research Engine</text>
<text class="rise r3 muted" x="58" y="208" font-size="19">Answers from your documents, with the sources they come from,</text>
<text class="rise r3 muted" x="58" y="236" font-size="19">and no answer when the evidence is not there.</text>
<g class="rise r3">
{pill(58, "pgvector · HNSW", p["accent_soft"], p["accent_fg"], 152)}
{pill(220, "hybrid search", p["panel"], p["muted"], 130)}
{pill(360, "measured in CI", p["rose_soft"], p["rose"], 140)}
</g>
{answer}{sources}
"""
    return card(
        340, "Research Engine: answers from your documents with their sources", style, body, p
    )


# --- results ---------------------------------------------------------------------------------


def results(p: dict[str, str], local: dict, cohere: dict, vector: dict) -> str:
    style = """
  .blink{animation:blink 2.8s ease-in-out infinite}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
  .grow{transform-box:fill-box;transform-origin:left;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}
  @keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  .pop{animation:pop .7s cubic-bezier(.2,.8,.2,1) both}
  @keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
"""
    x0, gap, top = 40, 24, 100
    pw = (W - 2 * x0 - 2 * gap) / 3
    ph = 300

    def panel(i: int, title: str, note: str) -> tuple[float, str]:
        x = x0 + i * (pw + gap)
        return x, (
            f'<rect x="{x}" y="{top}" width="{pw:.1f}" height="{ph}" rx="16" fill="{p["panel"]}" stroke="{p["border"]}"/>'
            f'<text x="{x + 20}" y="{top + 34}" font-size="16" class="h">{title}</text>'
            f'<text x="{x + 20}" y="{top + ph - 18}" font-size="11.5" class="mono faint">{note}</text>'
        )

    # Recall@5
    xa, a = panel(0, "Recall@5", "passage containing the answer in the top 5")
    rows = [
        ("Local · dense", local["modes"]["dense"]["all"]["recall@5"], p["dense"]),
        ("Local · hybrid", local["modes"]["hybrid"]["all"]["recall@5"], p["dense"]),
        ("Cohere · hybrid", cohere["modes"]["hybrid"]["all"]["recall@5"], p["lex"]),
        ("Cohere + rerank", cohere["modes"]["hybrid+rerank"]["all"]["recall@5"], p["accent"]),
    ]
    bw = pw - 40
    for j, (label, value, color) in enumerate(rows):
        y = top + 70 + j * 50
        a += (
            f'<text x="{xa + 20}" y="{y}" font-size="13" class="muted">{label}</text>'
            f'<text x="{xa + 20 + bw}" y="{y}" font-size="13" class="mono" text-anchor="end">{value:.2f}</text>'
            f'<rect x="{xa + 20}" y="{y + 9}" width="{bw:.1f}" height="9" rx="4.5" fill="{p["track"]}"/>'
            f'<rect class="grow" style="animation-delay:{0.15 * j:.2f}s" x="{xa + 20}" y="{y + 9}" '
            f'width="{bw * value:.1f}" height="9" rx="4.5" fill="{color}"/>'
        )

    # Abstention at the default (local) threshold
    xb, b = panel(
        1, "Abstention", f"local model · τ {local['abstention']['configured_threshold']:.2f}"
    )
    at = local["abstention"]["at_configured"]
    # cohere.json was produced before its threshold was calibrated: use the suggested (now default) one.
    co = cohere["abstention"]["suggested"]
    for j, (value, label, color) in enumerate(
        (
            (at["answerable_coverage"], "answerable questions answered", p["accent"]),
            (at["abstention_recall"], "unanswerable questions refused", p["rose"]),
        )
    ):
        y = top + 92 + j * 88
        b += (
            f'<text class="pop h" style="animation-delay:{0.2 * j:.1f}s" x="{xb + 20}" y="{y}" '
            f'font-size="44" fill="{color}">{value:.0%}</text>'
            f'<text x="{xb + 20}" y="{y + 24}" font-size="13" class="muted">{label}</text>'
        )
    b += (
        f'<text x="{xb + 20}" y="{top + 254}" font-size="12.5" class="muted">'
        f"Cohere · τ {co['threshold']:.2f}: {co['answerable_coverage']:.0%} answered, "
        f"{co['abstention_recall']:.0%} refused</text>"
    )

    # Search latency
    row = vector["results"][-1]
    xc, c = panel(2, f"Search · {row['chunks']:,} chunks", "median · same top 10 (recall@10 1.00)")
    old, new = row["legacy_python_p50_ms"], row["pgvector_hnsw_p50_ms"]
    c += (
        f'<text class="pop h" x="{xc + 20}" y="{top + 100}" font-size="40">'
        f'{old / 1000:.0f} s <tspan fill="{p["faint"]}">→</tspan> '
        f'<tspan fill="{p["accent"]}">{new:.0f} ms</tspan></text>'
        f'<text x="{xc + 20}" y="{top + 126}" font-size="13" class="muted">'
        f"{old / new:,.0f}× faster than v1</text>"
    )

    def log_w(ms: float) -> float:
        return (math.log10(max(ms, 1)) / 5) * bw

    for j, (label, ms, color) in enumerate(
        (("v1 · Python loop", old, p["rose"]), ("pgvector · HNSW", new, p["accent"]))
    ):
        y = top + 168 + j * 46
        value = f"{ms / 1000:.1f} s" if ms >= 1000 else f"{ms:.1f} ms"
        c += (
            f'<text x="{xc + 20}" y="{y}" font-size="13" class="muted">{label}</text>'
            f'<text x="{xc + 20 + bw}" y="{y}" font-size="13" class="mono" text-anchor="end">{value}</text>'
            f'<rect x="{xc + 20}" y="{y + 9}" width="{bw:.1f}" height="9" rx="4.5" fill="{p["track"]}"/>'
            f'<rect class="grow" style="animation-delay:{0.2 * j:.1f}s" x="{xc + 20}" y="{y + 9}" '
            f'width="{log_w(ms):.1f}" height="9" rx="4.5" fill="{color}"/>'
        )

    q = local["questions"]
    sub = f"{q['answerable'] + q['unanswerable']} questions · 26 PEPs · runs in CI"
    body = header("Results", sub, p) + a + b + c
    return card(top + ph + 40, "Benchmark results", style, body, p)


# --- how it works ----------------------------------------------------------------------------


def flow(p: dict[str, str]) -> str:
    style = """
  .blink{animation:blink 2.8s ease-in-out infinite}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
  .flowline{stroke-dasharray:5 9;animation:dash 1s linear infinite}
  @keyframes dash{to{stroke-dashoffset:-14}}
  .gate{transform-box:fill-box;transform-origin:center;animation:gate 3s ease-in-out infinite}
  @keyframes gate{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
"""

    def node(x: float, y: float, w: float, title: str, sub: str, kind: str = "n") -> str:
        fill, stroke = {
            "n": (p["panel"], p["border"]),
            "a": (p["accent_soft"], p["accent"]),
            "r": (p["rose_soft"], p["rose"]),
            "o": (p["panel"], p["line"]),
        }[kind]
        dash = ' stroke-dasharray="5 5"' if kind == "o" else ""
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="64" rx="14" fill="{fill}" stroke="{stroke}"{dash}/>'
            f'<text x="{x + w / 2}" y="{y + 28}" font-size="15" class="h" text-anchor="middle">{title}</text>'
            f'<text x="{x + w / 2}" y="{y + 48}" font-size="11.5" class="mono faint" text-anchor="middle">{sub}</text>'
        )

    def edge(d: str, color: str) -> str:
        return (
            f'<path d="{d}" fill="none" stroke="{p["line"]}" stroke-width="2"/>'
            f'<path class="flowline" d="{d}" fill="none" stroke="{color}" stroke-width="2" opacity=".8"/>'
        )

    # Ingest lane
    iy = 120
    ingest_nodes = [
        ("Upload", "safe names"), ("Queue", "SKIP LOCKED"), ("Chunk", "1,000 chars"),
        ("Embed", "local or Cohere"), ("Postgres", "vector · tsvector"),
    ]  # fmt: skip
    iw, ig = 176, 30
    ix0 = 150
    ingest_path = f"M{ix0 + iw / 2} {iy + 32}H{ix0 + 4 * (iw + ig) + iw / 2}"
    lane1 = (
        f'<text x="40" y="{iy + 38}" font-size="13" class="mono muted">ingest</text>'
        + edge(ingest_path, p["accent"])
        + f'<circle class="traveler" r="5" fill="{p["accent"]}"><animateMotion dur="7s" repeatCount="indefinite" path="{ingest_path}"/></circle>'
        + "".join(
            node(ix0 + i * (iw + ig), iy, iw, t, s, "a" if i == 4 else "n")
            for i, (t, s) in enumerate(ingest_nodes)
        )
    )

    # Ask lane
    ay = 260
    ask = (
        f'<text x="40" y="{ay + 38}" font-size="13" class="mono muted">ask</text>'
        + edge(f"M266 {ay + 32}C300 {ay + 32} 300 {ay - 6} 330 {ay - 6}", p["dense"])
        + edge(f"M266 {ay + 32}C300 {ay + 32} 300 {ay + 70} 330 {ay + 70}", p["lex"])
        + edge(f"M476 {ay - 6}C510 {ay - 6} 510 {ay + 32} 540 {ay + 32}", p["dense"])
        + edge(f"M476 {ay + 70}C510 {ay + 70} 510 {ay + 32} 540 {ay + 32}", p["lex"])
        + edge(f"M640 {ay + 32}H668", p["accent"])
        + edge(f"M800 {ay + 32}H836", p["accent"])
        + edge(f"M900 {ay + 32}H960", p["accent"])
        + edge(f"M868 {ay + 66}V{ay + 104}", p["rose"])
    )
    travel = (
        f"M266 {ay + 32}C300 {ay + 32} 300 {ay - 6} 330 {ay - 6}H476"
        f"C510 {ay - 6} 510 {ay + 32} 540 {ay + 32}H960"
    )
    ask += (
        f'<circle class="traveler" r="5" fill="{p["accent"]}"><animateMotion dur="6s" repeatCount="indefinite" path="{travel}"/></circle>'
        + node(150, ay, 116, "Question", "EN · ES")
        + f'<rect x="330" y="{ay - 30}" width="146" height="48" rx="12" fill="{p["panel"]}" stroke="{p["dense"]}"/>'
        + f'<text x="403" y="{ay}" font-size="14" class="h" text-anchor="middle">Dense</text>'
        + f'<rect x="330" y="{ay + 46}" width="146" height="48" rx="12" fill="{p["panel"]}" stroke="{p["lex"]}"/>'
        + f'<text x="403" y="{ay + 76}" font-size="14" class="h" text-anchor="middle">Lexical</text>'
        + node(540, ay, 100, "RRF", "fuse")
        + node(668, ay, 132, "Rerank", "optional", "o")
        + f'<g class="gate"><path d="M868 {ay - 2}L902 {ay + 32}L868 {ay + 66}L834 {ay + 32}Z" fill="{p["accent_soft"]}" stroke="{p["accent"]}" stroke-width="2"/></g>'
        + f'<text x="868" y="{ay + 37}" font-size="14" class="h" text-anchor="middle">τ</text>'
        + node(960, ay, 200, "Answer [n]", "citations checked", "a")
        + node(788, ay + 104, 160, "No answer", "model not called", "r")
    )

    body = header("How it works", "FastAPI · Postgres · worker", p) + lane1 + ask
    return card(450, "How it works: ingestion and question answering", style, body, p)


def main() -> None:
    local = json.loads((ROOT / "eval/results/baseline.json").read_text("utf-8"))
    cohere = json.loads((ROOT / "eval/results/cohere.json").read_text("utf-8"))
    vector = json.loads((ROOT / "docs/benchmarks/vector_search.json").read_text("utf-8"))
    for theme, palette in PALETTES.items():
        for name, content in (
            ("hero", hero(palette)),
            ("results", results(palette, local, cohere, vector)),
            ("flow", flow(palette)),
        ):
            (OUT / f"{name}-{theme}.svg").write_text(content, "utf-8", newline="\n")
    print(f"wrote 6 cards to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
