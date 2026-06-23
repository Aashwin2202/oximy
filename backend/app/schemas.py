from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class IngestEvent(BaseModel):
    """Loose inbound event. Tokens/cost optional — the server fills cost,
    confidence, and id when absent (used by the local-collector→remote-ingest
    flow and, later, the browser extension)."""

    id: str | None = None
    timestamp: datetime
    application: str
    provider: str = "unknown"
    model: str | None = None
    event_type: str = "message"
    capability: str = "chat"
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None
    estimated_cost: Decimal | None = None
    project: str | None = None
    confidence: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class AIEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    application: str
    provider: str
    model: str | None
    event_type: str
    capability: str
    input_tokens: int | None
    output_tokens: int | None
    cache_read_tokens: int | None
    cache_creation_tokens: int | None
    estimated_cost: Decimal | None
    project: str | None
    confidence: str
    metadata_json: dict


class EventPage(BaseModel):
    items: list[AIEventOut]
    next_cursor: str | None


class ConfidenceBreakdown(BaseModel):
    high: int = 0
    medium: int = 0
    low: int = 0


class DimensionCount(BaseModel):
    key: str
    events: int
    cost: Decimal
    tokens: int


class OverviewStats(BaseModel):
    total_events: int
    applications: int
    tools_used: int
    estimated_cost: Decimal
    total_tokens: int
    unknown_data_pct: float
    confidence: ConfidenceBreakdown
    by_application: list[DimensionCount]
    by_model: list[DimensionCount]
    date_range: dict[str, datetime | None]


class TimelinePoint(BaseModel):
    bucket: datetime
    events: int
    cost: Decimal
    tokens: int


class QualityStats(BaseModel):
    total_events: int
    with_token_data: int
    without_token_data: int
    with_cost: int
    without_cost: int
    unknown_models: list[str]
    confidence: ConfidenceBreakdown
    trust_score: float
    drift_events: int = 0


class LineageView(BaseModel):
    raw_source: dict
    parser: dict
    canonical_event: AIEventOut
    feeds_metrics: list[str]
