# Engineering Notes

What was built, what was deliberately deferred, and how each deferred item would be solved at scale.

## What's production-quality in this MVP

- **Canonical event model** — single stable schema, deterministic `source:message_id` dedup key, idempotent upsert via `ON CONFLICT DO UPDATE`. Re-running the collector never double-counts.
- **Dedup correctness** — global grouping by `message.id` across all JSONL files prevents the 2.4× inflation that per-file grouping would cause on resumed sessions.
- **Pricing versioning** — every priced event records `pricing_version` in `metadata_json`. A rate change is a reprice-by-version backfill job, not a silent overwrite of history.
- **Collection provenance** — upserts preserve the original `collector_run_id`/`collected_at` (first-seen) while recording `last_seen_run_id`/`last_seen_at` on re-ingest. Lineage traces to the specific collection pass.
- **Structured logging** — every collector run emits one audit line: `files= lines= json_errors= skipped_no_id= unique_events= drift=`. Silent drops are visible.
- **Bounded ingest** — `POST /ingest` rejects batches over `MAX_INGEST_BATCH` (default 5000) with 413.
- **Honest uncertainty** — sources without tokens get `null` cost and `low` confidence rather than estimated values that would corrupt ROI reports.
- **Privacy by default** — prompt text is never stored; only token counts, tool names, sha256 hashes, and classifications.

## Deliberately deferred (and why)

### In-memory global dedup
The collector holds all `message.id` groups in a Python dict for the duration of a scan. At single-user scale (~10K events) this is fine. At enterprise scale (billions of rows, multi-tenant), this must become:
- A streaming/windowed pass (dedup within a time window, then merge at DB layer)
- Or a DB-side dedup: ingest raw events, run a periodic dedup job that collapses by `message.id` and marks survivors

### Schema migrations (no Alembic)
`init_db()` calls `Base.metadata.create_all()` — correct for MVP, but not for production schema evolution. Before multi-deployment: introduce Alembic, make every migration additive and reversible, never rename/drop columns.

### Composite indexes
Keyset pagination (`events.py`) issues `WHERE (timestamp, id) < (ts, id)`. Without a composite `(timestamp DESC, id DESC)` index this becomes a full table scan at scale. Add the index when row count warrants.

### Per-client authentication
Currently a single global `INGEST_TOKEN`. Multi-tenant needs per-client keys with rotation, revocation, and per-key rate limits.

### Automated tests
The dedup logic, pricing computation, and late-arriving-data reconciliation are the highest-value targets for a test suite. No tests exist yet. First to write:
1. `test_dedup.py` — assert global grouping emits N unique events from M lines (M > N)
2. `test_pricing.py` — assert cost for known token counts against known rates; assert `pricing_version` stamped
3. `test_upsert.py` — assert second upsert of same event keeps original `collected_at`, updates `last_seen_at`

### Last-write-wins for late-arriving facts
If the same event arrives twice with different token counts (e.g., a corrected usage report from a vendor), the current upsert takes the latest values. This is correct for most cases but doesn't handle out-of-order delivery. A proper implementation compares `collected_at` timestamps and only updates revisable fields if the incoming event is newer.

### Content classification at scale
The "what are people actually doing" question (Oximy's "most of your coding work is in a tool you never approved") requires running models across the corpus. The canonical event schema has a `capability` field derived from tool names — a good start. Full classification needs throughput/cost controls, persisted verdicts so events are judged once not on every read, and an audit trail for disputed classifications.
