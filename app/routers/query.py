from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services import query_service

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    q: str
    k: int = 5
    threshold: float = 0.5
    max_tokens: int = 4000


@router.post("/query")
def query(req: QueryRequest, db: Session = Depends(get_db)):
    if not req.q or not req.q.strip():
        raise HTTPException(status_code=400, detail="Query text 'q' is required.")
    try:
        result = query_service.ask(db, req.q.strip(), top_k=req.k, threshold=req.threshold, max_tokens=req.max_tokens)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result
