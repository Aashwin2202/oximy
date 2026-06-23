# AI Usage Intelligence Dashboard

A unified view of AI tool usage across a company — **what** AI tools are used,
**how often**, **how much** they cost, and **how trustworthy** the usage data is.
Inspired by Oximy.

This MVP runs on **real data from your own machine** — it parses your actual
Claude Code sessions (`~/.claude/projects/*/*.jsonl`). No mock data, no fake
events, no sample analytics.

> Verified locally: **~3,683 real events**, 15 distinct tools, **~$191 estimated
> spend**, 355M tokens, over ~7 weeks of activity — **99.8% data trust score**.

---

## What it shows

- **Overview** — total interactions, applications, distinct tools, estimated
  spend, total tokens, unknown-data %, and a confidence breakdown.
- **Timeline** — daily activity (toggle between events / tokens / cost).
- **Event Explorer** — filterable event table; click any row to see its
  **lineage**: raw source hash → parser → canonical event → the metrics it feeds.
- **Data Quality** — token coverage, unpriceable models, trust score. Answers
  "how much of this can I believe?"

## Stack

FastAPI · PostgreSQL · SQLAlchemy · Pydantic · React · TypeScript · Tailwind ·
Recharts · Docker Compose.

See [architecture.md](architecture.md) for the data flow and the canonical event model.

---

## Run locally (Docker)

```bash
cp .env.example .env          # optional: set INGEST_TOKEN
docker compose up --build -d  # starts db + backend + frontend
```

Seed it with your **real** Claude Code usage (mounts `~/.claude` read-only):

```bash
docker compose run --rm backend python -m app.collectors.run_collector
```

Open the dashboard at **http://localhost:5173**.
Backend API + docs: **http://localhost:8000/docs**.

Re-running the collector is idempotent (upsert by event id), so run it again
anytime to pick up new sessions.

### Privacy

Prompt and response **text is never stored**. The collector keeps token counts,
tool names, classifications, and a `sha256` of each raw line (for lineage).
Setting `DEBUG_RAW=true` only lets the lineage view note that raw inspection is
enabled — it still never persists prompt text.

---

## Deploy a shareable demo (local collector → remote ingest)

The cloud database can't read your laptop's `~/.claude`. So the honest flow is:
run the collector **locally** and push the parsed canonical events (tokens, cost,
metadata — **no prompts**) to a deployed backend.

1. **Backend + Postgres → Railway.** New project → deploy `backend/` → add a
   Postgres plugin → set `DATABASE_URL` (Railway provides it; the app reads
   `DATABASE_URL`), `INGEST_TOKEN`, and `CORS_ORIGINS=<your Vercel URL>`.
2. **Frontend → Vercel.** Import `frontend/`, set `VITE_API_URL=<Railway backend URL>`.
3. **Push your real data up from your laptop:**

   ```bash
   cd backend
   pip install -e .   # or use the docker image
   python -m app.collectors.run_collector \
       --claude-dir ~/.claude \
       --ingest-url https://<your-backend>.up.railway.app \
       --ingest-token <INGEST_TOKEN>
   ```

   This POSTs canonical events to `/ingest`. Only token counts, tool names,
   hashes, and classifications leave your machine.

Share the Vercel URL.

---

## Limitations & future improvements

- **Costs are estimated**, not billed — tokens × published per-model pricing.
- **Claude Code is the only live collector** in this MVP. The architecture is
  source-agnostic (everything becomes a canonical event via `/ingest`), so:
  - **Browser AI (Phase 2):** a Chrome extension for ChatGPT / Claude web /
    Notion AI / Canva AI. It can only capture *live* activity you generate, and
    those sites expose no token counts → medium/low confidence. Scaffolded, not
    built here.
  - **API collectors (Phase 3):** OpenAI / Anthropic API usage — needs API keys
    (none present in this environment).
  - **Codex CLI:** local data exists but is sparse; a best-effort low-confidence
    collector is future work.
- Cloud demo shows a **snapshot** pushed from your laptop; a scheduled push or a
  hosted collector would keep it live.
