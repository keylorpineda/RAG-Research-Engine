"""The benchmark corpus: Python Enhancement Proposals, pinned to one commit of python/peps.

PEPs are public domain (or CC0), technical, written by many authors, and full of the exact
identifiers (``TypeVarTuple``, ``__future__``, ``:=``) that separate lexical from dense retrieval.

    uv run python -m eval.corpus          # download into eval/corpus/ and verify checksums
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

PEPS_COMMIT = "3b0eaa2021d57747ab83b9356eefe597c5745dde"
PEPS = (
    8, 20, 257, 343, 380, 405, 435, 448, 484, 492, 498, 526, 557,
    572, 584, 585, 604, 618, 634, 646, 655, 673, 695, 701, 703, 723,
)  # fmt: skip
BASE_URL = f"https://raw.githubusercontent.com/python/peps/{PEPS_COMMIT}/peps"
ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "corpus"
LOCK_FILE = ROOT / "corpus.lock.json"


def filename(pep: int) -> str:
    return f"pep-{pep:04d}.rst"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(*, update_lock: bool = False) -> list[Path]:
    """Download missing files and check every file against the lock."""
    lock: dict[str, str] = json.loads(LOCK_FILE.read_text("utf-8")) if LOCK_FILE.exists() else {}
    CORPUS_DIR.mkdir(exist_ok=True)
    paths = []
    for pep in PEPS:
        path = CORPUS_DIR / filename(pep)
        if not path.exists():
            url = f"{BASE_URL}/{path.name}"
            with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 (fixed https URL)
                path.write_bytes(response.read())
        digest = _sha256(path.read_bytes())
        if update_lock:
            lock[path.name] = digest
        elif lock.get(path.name) != digest:
            raise RuntimeError(f"{path.name} does not match corpus.lock.json; delete it and rerun")
        paths.append(path)
    if update_lock:
        LOCK_FILE.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", "utf-8")
    return paths


if __name__ == "__main__":
    files = fetch(update_lock="--update-lock" in sys.argv)
    size = sum(p.stat().st_size for p in files)
    print(f"{len(files)} PEPs, {size / 1024:.0f} KiB, commit {PEPS_COMMIT[:12]}")
