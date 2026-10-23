import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import worker
from app.core.config import settings
from app.core.errors import install_error_handling
from app.routers import documents, health, query, upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    stop = threading.Event()
    thread = None
    if settings.embedded_worker:
        thread = threading.Thread(target=worker.run, args=(stop,), name="worker", daemon=True)
        thread.start()
    yield
    stop.set()
    if thread is not None:
        thread.join(timeout=10)


app = FastAPI(
    title="RAG Research Engine",
    description="Retrieval-augmented question answering over your own documents.",
    version="2.2.3",
    lifespan=lifespan,
)

install_error_handling(app)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(health.router)
