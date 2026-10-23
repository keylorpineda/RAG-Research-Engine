#!/bin/sh
# api (default): apply migrations, load the PEPs if SEED_CORPUS=true, then serve on $PORT
# (hosts like Render set it; 8000 otherwise).
# worker: run the ingestion worker. Anything else runs as a command.
set -e

case "$1" in
  api)
    alembic upgrade head
    # Demo hosts without a shell or outside database access load the PEPs here; idempotent and
    # a single query once they are in.
    if [ "${SEED_CORPUS:-false}" = "true" ]; then
      python -m eval.seed
    fi
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers \
      --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
    ;;
  worker)
    exec python -m app.worker
    ;;
  *)
    exec "$@"
    ;;
esac
