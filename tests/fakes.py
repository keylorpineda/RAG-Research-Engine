"""Deterministic stand-ins for model providers."""

import hashlib
import math
import re
from collections.abc import Sequence

_TOKEN = re.compile(r"\w+", re.UNICODE)


class HashEmbeddings:
    """Bag of hashed words: texts sharing words get similar vectors. No model, no network."""

    name = "fake:hash"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            vector[int.from_bytes(digest[:4]) % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
