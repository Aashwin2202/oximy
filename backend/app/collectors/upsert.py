"""Shared idempotent upsert for canonical AI events.

On conflict (same event id), revisable facts (tokens, cost, confidence, model)
are updated to the latest values, but original collection provenance is
preserved: collected_at and collector_run_id always reflect the FIRST time this
event was seen. The most recent pass is recorded as last_seen_at/last_seen_run_id.
"""

import logging

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import AIEvent

log = logging.getLogger(__name__)

# Columns updated on re-ingest. Omit id/created_at (immutable) and
# metadata_json (handled separately with provenance-preserving merge).
_REVISABLE = {
    c.name
    for c in AIEvent.__table__.columns
    if c.name not in ("id", "created_at", "metadata_json")
}


def upsert_events(db: Session, rows: list[dict]) -> int:
    """Upsert rows in chunks of 500. Returns total rows processed.

    Provenance contract: metadata_json is merged, not replaced.
    - Start with the stored (existing) metadata_json.
    - Overlay the incoming payload (tools, hashes, drifts, pricing_version update).
    - Pin collector_run_id/collected_at back to the original first-seen values.
    - Set last_seen_run_id/last_seen_at to the incoming run.

    JSONB || merges right-over-left, so later keys win. Order:
      stored || incoming || {pinned_first_seen, last_seen}
    """
    if not rows:
        return 0

    written = 0
    for i in range(0, len(rows), 500):
        chunk = rows[i : i + 500]
        stmt = insert(AIEvent).values(chunk)

        update_cols: dict = {col: stmt.excluded[col] for col in _REVISABLE}

        # Build the provenance-preserving merge expression.
        # The rightmost || wins, so pinned first-seen keys come last.
        stored = AIEvent.metadata_json
        incoming = stmt.excluded.metadata_json

        update_cols["metadata_json"] = (
            stored
            .op("||")(incoming)
            .op("||")(
                func.jsonb_build_object(
                    text("'collector_run_id'"),
                    # Preserve original; fall back to incoming on true first insert
                    # (conflict branch only fires on actual collision, so stored
                    # collector_run_id is always non-null at this point).
                    func.coalesce(
                        stored[text("'collector_run_id'")],
                        incoming[text("'collector_run_id'")],
                    ),
                    text("'collected_at'"),
                    func.coalesce(
                        stored[text("'collected_at'")],
                        incoming[text("'collected_at'")],
                    ),
                    text("'last_seen_run_id'"),
                    incoming[text("'collector_run_id'")],
                    text("'last_seen_at'"),
                    incoming[text("'collected_at'")],
                )
            )
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=update_cols,
        )
        try:
            db.execute(stmt)
            written += len(chunk)
            log.debug("upserted chunk of %d events", len(chunk))
        except Exception:
            log.exception("upsert failed on chunk %d-%d", i, i + len(chunk))
            raise

    try:
        db.commit()
    except Exception:
        log.exception("commit failed after upserting %d events", written)
        raise

    return written
