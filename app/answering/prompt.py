"""The grounded-answer prompt.

Short on purpose. The v1 prompt asked for an executive summary, a detailed analysis with tables
and a sources section, which pushes a model to produce content even when the passages are thin.
Here the model either answers from numbered passages, citing them by number, or says it cannot.
"""

from collections.abc import Sequence

from app.retrieval.dense import Hit

NO_ANSWER = "NO_ANSWER"

SYSTEM_PROMPT = f"""You answer questions using only the numbered passages you are given.

Rules:
- Use only facts stated in the passages. Do not add knowledge of your own.
- After every sentence that uses a passage, cite it by number in brackets: [2] or [1][3].
- If the passages do not contain the answer, reply with exactly {NO_ANSWER} and nothing else.
- Answer in the language of the question. Keep code, names and technical terms as written.
- Be direct and concise: a short paragraph or a short list."""


def build_user_prompt(question: str, passages: Sequence[Hit]) -> str:
    blocks = [
        f"[{n}] {p.filename} (chunk {p.chunk_index})\n{p.text.strip()}"
        for n, p in enumerate(passages, start=1)
    ]
    return "Passages:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question.strip()}"
