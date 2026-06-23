# Architecture

```
AI Sources (real, on your machine)
   └─ Claude Code sessions:  ~/.claude/projects/*/*.jsonl
            │
            ▼
Collector  (backend/app/collectors/claude_code.py)
   • walks JSONL, keeps type=="assistant"
   • DEDUP by message.id (taken once across streamed lines AND files)
   • derives event_type + capability from tool_use names
   • computes cost from tokens × per-model pricing (pricing.py)
   • assigns confidence (high / medium / low)
   • privacy: stores token counts + tool names + sha256(line) — never prompt text
            │
            ▼
Canonical AI Event  (one standard shape for every interaction)
   { id, timestamp, application, provider, model, event_type, capability,
     input/output/cache tokens, estimated_cost, project, confidence, metadata }
            │
            ▼  (idempotent upsert: INSERT ... ON CONFLICT (id) DO UPDATE)
PostgreSQL  (table: ai_events)
            │
            ▼
FastAPI backend  (backend/app)
   /ingest                 POST canonical events (bearer token)
   /events  /events/{id}/lineage
   /stats/overview  /stats/timeline  /stats/by-dimension  /stats/quality
            │
            ▼
React + TypeScript + Tailwind + Recharts dashboard
   Overview · Timeline · Event Explorer (raw→parser→canonical→metric) · Data Quality
```

## Why dedup is the load-bearing detail

Claude Code writes one JSONL line per streamed chunk. Many lines share a single
`message.id` and **repeat identical usage** (verified: 6 lines, all `123`
output tokens). The same `message.id` can also recur across files when a session
is resumed/branched. The collector groups globally by `message.id` and takes
usage **once** — summing would inflate cost by ~2.4× and double-count events.

## Representing uncertainty

Not every source has the same data. The system encodes that instead of faking it:

| Source        | Model | Tokens | Cost      | Confidence |
| ------------- | ----- | ------ | --------- | ---------- |
| Claude Code   | yes   | yes    | computed  | **high**   |
| (`<synthetic>` local events) | n/a | n/a | null | **low** |
| Browser AI (future) | no | no | estimated/null | medium/low |

Costs are **estimated** (tokens × published pricing), not billed.
