from fastapi import APIRouter, Depends, HTTPException
import pathlib

from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import Document

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "mime": d.mime,
            "size": d.size,
            "status": d.status,
            "uploadTs": d.upload_ts.isoformat() if d.upload_ts else None,
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "mime": doc.mime,
        "size": doc.size,
        "status": doc.status,
        "uploadTs": doc.upload_ts.isoformat() if doc.upload_ts else None,
        "chunks": [
            {
                "id": c.id,
                "chunkIndex": c.chunk_index,
                "tokenCount": c.token_count,
                "text": c.text,
            }
            for c in doc.chunks
        ],
    }


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        path = pathlib.Path(doc.path)
        if path.exists():
            path.unlink()
    except Exception:
        pass
        
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}

