from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.logging_config import configure_logging

configure_logging()
from fastapi.middleware.cors import CORSMiddleware

from app.api import events, ingest, stats
from app.config import get_settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Usage Intelligence Dashboard", lifespan=lifespan)

_origins = get_settings().cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")] if _origins != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(events.router)
app.include_router(stats.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
