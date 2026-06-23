import base64
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import AIEvent
from app.schemas import AIEventOut, EventPage, LineageView

router = APIRouter(tags=["events"])


def _encode_cursor(ts: datetime, id_: str) -> str:
    return base64.urlsafe_b64encode(f"{ts.isoformat()}|{id_}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    ts_str, id_ = raw.split("|", 1)
    return datetime.fromisoformat(ts_str), id_


@router.get("/events", response_model=EventPage)
def list_events(
    db: Session = Depends(get_db),
    application: str | None = None,
    model: str | None = None,
    capability: str | None = None,
    confidence: str | None = None,
    project: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    cursor: str | None = None,
    limit: int = Query(50, le=200),
) -> EventPage:
    stmt = select(AIEvent)
    if application:
        stmt = stmt.where(AIEvent.application == application)
    if model:
        stmt = stmt.where(AIEvent.model == model)
    if capability:
        stmt = stmt.where(AIEvent.capability == capability)
    if confidence:
        stmt = stmt.where(AIEvent.confidence == confidence)
    if project:
        stmt = stmt.where(AIEvent.project == project)
    if start:
        stmt = stmt.where(AIEvent.timestamp >= start)
    if end:
        stmt = stmt.where(AIEvent.timestamp <= end)

    # Stable ordering for keyset pagination: newest first.
    stmt = stmt.order_by(AIEvent.timestamp.desc(), AIEvent.id.desc())
    if cursor:
        ts, id_ = _decode_cursor(cursor)
        stmt = stmt.where(
            (AIEvent.timestamp < ts)
            | ((AIEvent.timestamp == ts) & (AIEvent.id < id_))
        )

    rows = db.execute(stmt.limit(limit + 1)).scalars().all()
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.timestamp, last.id)
        rows = rows[:limit]

    return EventPage(
        items=[AIEventOut.model_validate(r) for r in rows],
        next_cursor=next_cursor,
    )


@router.get("/events/{event_id}/lineage", response_model=LineageView)
def event_lineage(event_id: str, db: Session = Depends(get_db)) -> LineageView:
    """Trace one event: raw source hash -> parser-derived fields -> canonical
    event -> the dashboard metrics it feeds."""
    row = db.get(AIEvent, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")

    settings = get_settings()
    meta = row.metadata_json or {}
    raw_source = {
        "source": row.id.split(":", 1)[0],
        "raw_line_sha256": meta.get("raw_hash"),
        "session_id": meta.get("session_id"),
        "collector_run_id": meta.get("collector_run_id"),
        "collected_at": meta.get("collected_at"),
        "last_seen_run_id": meta.get("last_seen_run_id"),
        "last_seen_at": meta.get("last_seen_at"),
        "user": meta.get("user", "local"),
        "identity_status": meta.get("identity_status", "unresolved"),
        "identity_note": meta.get("identity_note"),
        "schema_drifts": meta.get("schema_drifts", []),
        "note": "Raw prompt/response text is never stored. Only this hash is kept.",
    }
    if settings.debug_raw:
        raw_source["debug_raw_enabled"] = True

    parser = {
        "deduped_by": "message.id (taken once across streamed lines and files)",
        "tools_observed": meta.get("tools", []),
        "model": row.model,
        "derived_event_type": row.event_type,
        "derived_capability": row.capability,
        "cost_method": "tokens x per-model pricing (input/output/cache split)",
        "pricing_version": meta.get("pricing_version"),
        "confidence_rule": row.confidence,
    }
    feeds = [
        "Overview: total interactions / cost / tokens",
        f"By model: {row.model or 'unknown'}",
        f"By capability: {row.capability}",
        "Timeline (by day)",
        "Data Quality: token coverage + trust score",
    ]
    return LineageView(
        raw_source=raw_source,
        parser=parser,
        canonical_event=AIEventOut.model_validate(row),
        feeds_metrics=feeds,
    )
