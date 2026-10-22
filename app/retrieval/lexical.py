"""Lexical retrieval with Postgres full-text search.

Catches what embeddings blur: identifiers, acronyms, numbers and rare names (``PEP 572``,
``TypeVarTuple``, ``__future__``). The ``simple`` configuration does no stemming, so it behaves
the same for English and Spanish text.
"""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.models import DocChunk, Document, DocumentStatus
from app.retrieval.dense import Hit

_WORD = re.compile(r"\w+", re.UNICODE)
MAX_TERMS = 32

# Function words that carry no topic in English and Spanish questions. With OR semantics they
# would match almost every chunk.
STOPWORDS = frozenset(
    """
    a an and are as at be by can could do does did for from has have how i if in into is it its
    me my no not of on or our should so than that the their them then there these they this to
    was we were what when where which who whom why will with would you your about after before
    between both each more most other some such only own same too very just also any all al como
    con cual cuales cuando de del donde el ella ellos en entre era es esa ese eso esta este esto
    fue ha hay la las le les lo los mas mi mis muy no nos o para pero por que quien se sea ser
    si sin sobre son su sus tambien te tiene tu un una uno unos unas y ya qué cómo cuál cuáles
    cuándo dónde quién más sí también está están
    """.split()  # noqa: SIM905 (one word list is easier to read and edit)
)


def to_tsquery_text(question: str) -> str | None:
    """OR of the meaningful words of ``question``, safe to pass to ``to_tsquery``.

    ``websearch_to_tsquery`` requires every word to be present, which almost never happens for a
    natural-language question. Words are reduced to ``\\w+`` tokens, so operators and quotes in
    the input cannot change the query.
    """
    terms: list[str] = []
    for token in _WORD.findall(question.lower()):
        if (len(token) > 1 or token.isdigit()) and token not in STOPWORDS and token not in terms:
            terms.append(token)
    return " | ".join(terms[:MAX_TERMS]) or None


def lexical_search(db: Session, question: str, *, k: int) -> list[Hit]:
    """Top ``k`` chunks of READY documents by ``ts_rank_cd`` (cover density, length-normalized)."""
    query_text = to_tsquery_text(question)
    if query_text is None:
        return []
    tsquery = func.to_tsquery("simple", query_text)
    rank = func.ts_rank_cd(DocChunk.tsv, tsquery, 1)  # 1: divide by 1 + log(length)
    rows = db.execute(
        select(
            DocChunk.id,
            DocChunk.document_id,
            Document.filename,
            DocChunk.chunk_index,
            DocChunk.text,
            DocChunk.token_count,
            rank.label("score"),
            DocChunk.section,
        )
        .join(Document)
        .where(Document.status == DocumentStatus.READY, DocChunk.tsv.bool_op("@@")(tsquery))
        .order_by(rank.desc(), DocChunk.id)
        .limit(k)
    ).all()
    return [Hit(*row) for row in rows]
