from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import QueryLog
from app.providers.embeddings import get_embedding_provider
from app.retrieval.dense import Hit, dense_search
from app.retrieval.ranking import Scored, select_passages
from app.services import llm_provider

# Retrieve more than k so the token budget can skip long passages and still fill k slots.
CANDIDATE_FACTOR = 4


def ask(
    db: Session, question: str, top_k: int = 5, threshold: float = 0.3, max_tokens: int = 4000
) -> dict[str, Any]:
    query_vector = get_embedding_provider().embed_query(question)
    hits = dense_search(
        db, query_vector, k=top_k * CANDIDATE_FACTOR, ef_search=settings.hnsw_ef_search
    )
    selected = select_passages(
        (Scored(h, h.score, h.token_count) for h in hits),
        top_k=top_k,
        max_tokens=max_tokens,
        min_score=threshold,
    )
    top: list[tuple[Hit, float]] = [(s.item, s.score) for s in selected]

    context_parts = []
    for chunk, score in top:
        context_parts.append(f"- [{chunk.filename}] (score: {score:.4f}): {chunk.text}")
    context = "\n".join(context_parts)

    prompt = f"""Eres el Senior AI Research Lead. Tu propósito es realizar análisis técnicos basados EXCLUSIVAMENTE en el contexto.

Reglas de Oro:
1. Detección de Idioma: Responde siempre en el idioma de la pregunta del usuario. Si los documentos están en otro idioma, traduce el contenido pero mantén términos técnicos originales entre paréntesis.
2. Citas Obligatorias: Cada dato debe ir seguido de su fuente, ejemplo: [nombre_del_archivo.pdf].
3. Cero Alucinación: Si la info no está en el contexto, indica textualmente: "La información solicitada no se encuentra en los documentos de investigación actuales." No inventes información.
4. Estructura de Salida:
   1. **Resumen Ejecutivo**: Una sola oración con la respuesta directa.
   2. **Análisis Detallado**: Cuerpo de la investigación usando Markdown (negritas, tablas, listas).
   3. **Fuentes Consultadas**: Lista numerada de los archivos utilizados.

Contexto Recuperado:
{context}

Pregunta del Usuario: {question}"""

    answer = llm_provider.chat(prompt)
    if not answer or not answer.strip():
        answer = "The Research Engine returned an empty response. This might be due to safety filters or context issues."

    references = [
        {
            "docId": chunk.document_id,
            "filename": chunk.filename,
            "chunkIndex": chunk.chunk_index,
            "score": round(score, 6),
            "text": chunk.text,
        }
        for chunk, score in top
    ]

    log = QueryLog(
        query_text=question,
        result_refs=references,
    )
    db.add(log)
    db.commit()

    return {"answer": answer, "refs": references}
