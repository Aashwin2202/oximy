#!/bin/sh
# Wait for the database to be ready.
set -e

MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
  if python -c "from app.db import engine; engine.execute('SELECT 1')" 2>/dev/null; then
    break
  fi
  RETRY=$((RETRY + 1))
  echo "Waiting for database... ($RETRY/$MAX_RETRIES)"
  sleep 1
done

if [ $RETRY -eq $MAX_RETRIES ]; then
  echo "Database failed to start after $MAX_RETRIES attempts"
  exit 1
fi

# Run collector once at startup, then every 2 minutes in the background.
python -m app.collectors.run_collector

(
  while true; do
    sleep 120
    python -m app.collectors.run_collector
  done
) &

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
