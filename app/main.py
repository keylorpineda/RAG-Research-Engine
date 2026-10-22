import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.errors import install_error_handling
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

install_error_handling(app)
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(query.router)
