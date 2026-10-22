#!/bin/sh
# api (default): apply migrations, then serve on $PORT (hosts like Render set it; 8000 otherwise).
# worker: run the ingestion worker. Anything else runs as a command.
set -e

case "$1" in
  api)
    alembic upgrade head
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
