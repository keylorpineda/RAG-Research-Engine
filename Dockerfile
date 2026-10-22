FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

# "local" installs the on-device embedding runtime. EXTRAS=none builds an image that only talks
# to hosted providers (Cohere): smaller, and it fits a 512 MB instance.
ARG EXTRAS=local

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    MODEL_CACHE_DIR=/app/models

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN if [ "$EXTRAS" = "none" ]; then extra=""; else extra="--extra $EXTRAS"; fi; \
    uv sync --frozen --no-dev --no-install-project $extra

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY docker-entrypoint.sh ./
# The corpus loader, for a demo instance: docker compose exec api python -m eval.seed
COPY eval/__init__.py eval/corpus.py eval/corpus.lock.json eval/seed.py ./eval/

RUN useradd --create-home --uid 1000 rag \
    && mkdir -p /app/uploads /app/models /app/eval/corpus \
    && chown rag /app/uploads /app/models /app/eval/corpus
USER rag

EXPOSE 8000

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
CMD ["api"]
