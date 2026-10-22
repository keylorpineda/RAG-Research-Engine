import json
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.models import DocChunk, Document, Embedding, QueryLog
from app.providers.embeddings import get_embedding_provider
from app.retrieval.ranking import Scored, select_passages
from app.services import llm_provider, similarity


def ask(
    db: Session, question: str, top_k: int = 5, threshold: float = 0.3, max_tokens: int = 4000
) -> dict[str, Any]:
    query_vector = get_embedding_provider().embed_query(question)

    chunks = (
        db.query(DocChunk)
        .options(joinedload(DocChunk.document))
        .join(Document)
        .filter(Document.status == "READY")
        .all()
    )
    chunks_by_id = {c.id: c for c in chunks}

    embeddings = (
        db.query(Embedding).join(DocChunk).join(Document).filter(Document.status == "READY").all()
    )

    candidates: list[Scored[DocChunk]] = []
    for emb in embeddings:
        chunk = chunks_by_id.get(emb.chunk_id)
        if chunk is None:
            continue
        vector = emb.vector if isinstance(emb.vector, list) else json.loads(emb.vector)
        candidates.append(Scored(chunk, similarity.cosine(query_vector, vector), chunk.token_count))

    top = [
        (s.item, s.score)
        for s in select_passages(
            candidates, top_k=top_k, max_tokens=max_tokens, min_score=threshold
        )
    ]

    context_parts = []
    for chunk, score in top:
        filename = chunk.document.filename if chunk.document else "unknown"
        context_parts.append(f"- [{filename}] (score: {score:.4f}): {chunk.text}")
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
            "filename": chunk.document.filename if chunk.document else "unknown",
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
