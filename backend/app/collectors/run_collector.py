"""Run the Claude Code collector.

Two modes:

  # Write straight into the configured database (local / seed Railway):
  python -m app.collectors.run_collector

  # POST canonical events to a deployed backend (no DB access needed locally):
  python -m app.collectors.run_collector --ingest-url https://api.example.com \
      --ingest-token <token>

Either way, no prompt text leaves the machine — only token counts, tool names,
hashes, and classifications.
"""

import argparse
import datetime as dt
import json
import logging
import os
import urllib.request

from app.collectors.claude_code import iter_canonical_events
from app.config import get_settings
from app.logging_config import configure_logging

configure_logging()
log = logging.getLogger(__name__)


def _json_default(o):
    from decimal import Decimal

    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (dt.datetime, dt.date)):
        return o.isoformat()
    raise TypeError(f"not serializable: {type(o)}")


def _write_to_db(events: list[dict]) -> int:
    from app.collectors.upsert import upsert_events
    from app.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as db:
        written = upsert_events(db, events)
    return written


def _post_to_remote(events: list[dict], url: str, token: str, chunk_size: int = 500) -> int:
    """POST events in chunks to avoid hitting the server's max_ingest_batch limit."""
    total = 0
    for i in range(0, len(events), chunk_size):
        chunk = events[i : i + chunk_size]
        payload = json.dumps(chunk, default=_json_default).encode("utf-8")
        req = urllib.request.Request(
            url.rstrip("/") + "/ingest",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read())
            total += body.get("ingested", 0)
            log.debug("posted chunk %d-%d: %d ingested", i, i + len(chunk), body.get("ingested", 0))
        except Exception:
            log.exception("failed to post chunk %d-%d to %s", i, i + len(chunk), url)
            raise
    return total


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Collect real Claude Code usage.")
    parser.add_argument("--claude-dir", default=settings.claude_dir)
    parser.add_argument("--ingest-url", default=os.environ.get("INGEST_URL"))
    parser.add_argument("--ingest-token", default=settings.ingest_token)
    args = parser.parse_args()

    log.info("collector starting: claude_dir=%s", args.claude_dir)
    events = list(iter_canonical_events(args.claude_dir))
    log.info("collector parsed: unique_events=%d claude_dir=%s", len(events), args.claude_dir)

    if not events:
        log.warning("no events found — is the Claude directory mounted correctly? path=%s", args.claude_dir)
        return

    if args.ingest_url:
        n = _post_to_remote(events, args.ingest_url, args.ingest_token)
        log.info("collector complete: ingested=%d target=%s", n, args.ingest_url)
    else:
        n = _write_to_db(events)
        log.info("collector complete: upserted=%d target=db", n)


if __name__ == "__main__":
    main()
