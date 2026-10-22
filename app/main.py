import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import documents, query, upload
from app.services.ingestion import start_background_ingestion, stop_background_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    start_background_ingestion()
    yield
    stop_background_ingestion()


app = FastAPI(
    title="RAG Research Engine",
    description="Retrieval-augmented question answering over your own documents.",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
