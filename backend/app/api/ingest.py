import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.collectors.base import finalize_cost_and_confidence
from app.collectors.upsert import upsert_events
from app.config import get_settings
from app.db import get_db
from app.schemas import IngestEvent

log = logging.getLogger(__name__)
router = APIRouter(tags=["ingest"])


def _require_token(authorization: str | None = Header(default=None)) -> None:
    expected = get_settings().ingest_token
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Invalid or missing ingest token")


@router.post("/ingest")
def ingest(
    events: list[IngestEvent],
    db: Session = Depends(get_db),
    _: None = Depends(_require_token),
) -> dict:
    """Upsert a batch of canonical events. Server fills id/cost/confidence when
    the caller omits them, so thin sources (browser extension) work too."""
    settings = get_settings()
    if len(events) > settings.max_ingest_batch:
        raise HTTPException(
            status_code=413,
            detail=f"Batch too large ({len(events)} events). Max is {settings.max_ingest_batch}. Split into smaller batches.",
        )

    rows: list[dict] = []
    for ev in events:
        data = ev.model_dump()
        if not data.get("id"):
            mid = data["metadata_json"].get("raw_hash") or data["timestamp"].isoformat()
            data["id"] = f"{data['application'].lower().replace(' ', '_')}:{mid}"
        data = finalize_cost_and_confidence(data)
        rows.append(data)

    if not rows:
        return {"ingested": 0}

    log.info("ingest request: %d events", len(rows))
    written = upsert_events(db, rows)
    log.info("ingest complete: %d events written", written)
    return {"ingested": written}
