#!/bin/sh
# Run collector once at startup, then every 2 minutes in the background.
python -m app.collectors.run_collector

(
  while true; do
    sleep 120
    python -m app.collectors.run_collector
  done
) &

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
