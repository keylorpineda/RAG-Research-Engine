from fastapi import APIRouter

from app.core.errors import BadRequestError
from app.models.database import DbSession
from app.schemas import QueryRequest, QueryResponse
from app.services import query_service

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
def query(req: QueryRequest, db: DbSession) -> QueryResponse:
    question = req.q.strip()
    if not question:
        raise BadRequestError("The question cannot be empty.")
    result = query_service.ask(
        db,
        question,
        top_k=req.k,
        threshold=req.threshold,
        max_tokens=req.max_tokens,
        mode=req.mode,
    )
    return QueryResponse.model_validate(result)
