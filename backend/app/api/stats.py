from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AIEvent
from app.schemas import (
    ConfidenceBreakdown,
    DimensionCount,
    OverviewStats,
    QualityStats,
    TimelinePoint,
)

router = APIRouter(tags=["stats"])

_TOKENS = (
    func.coalesce(AIEvent.input_tokens, 0)
    + func.coalesce(AIEvent.output_tokens, 0)
    + func.coalesce(AIEvent.cache_read_tokens, 0)
    + func.coalesce(AIEvent.cache_creation_tokens, 0)
)


def _confidence(db: Session) -> ConfidenceBreakdown:
    rows = db.execute(
        select(AIEvent.confidence, func.count()).group_by(AIEvent.confidence)
    ).all()
    cb = ConfidenceBreakdown()
    for conf, n in rows:
        setattr(cb, conf, n)
    return cb


def _dimension(db: Session, col) -> list[DimensionCount]:
    rows = db.execute(
        select(
            col,
            func.count(),
            func.coalesce(func.sum(AIEvent.estimated_cost), 0),
            func.coalesce(func.sum(_TOKENS), 0),
        )
        .group_by(col)
        .order_by(func.count().desc())
    ).all()
    return [
        DimensionCount(
            key=str(key) if key is not None else "unknown",
            events=n,
            cost=Decimal(cost),
            tokens=int(tokens),
        )
        for key, n, cost, tokens in rows
    ]


@router.get("/stats/overview", response_model=OverviewStats)
def overview(db: Session = Depends(get_db)) -> OverviewStats:
    total = db.execute(select(func.count()).select_from(AIEvent)).scalar_one()
    apps = db.execute(select(func.count(func.distinct(AIEvent.application)))).scalar_one()
    cost = db.execute(
        select(func.coalesce(func.sum(AIEvent.estimated_cost), 0))
    ).scalar_one()
    tokens = db.execute(select(func.coalesce(func.sum(_TOKENS), 0))).scalar_one()
    no_tokens = db.execute(
        select(func.count()).where(AIEvent.input_tokens.is_(None))
    ).scalar_one()

    # Count distinct tool names across all events' metadata.
    tool_rows = db.execute(select(AIEvent.metadata_json["tools"])).all()
    tools: set[str] = set()
    for (arr,) in tool_rows:
        if arr:
            tools.update(arr)

    rng = db.execute(
        select(func.min(AIEvent.timestamp), func.max(AIEvent.timestamp))
    ).one()

    return OverviewStats(
        total_events=total,
        applications=apps,
        tools_used=len(tools),
        estimated_cost=Decimal(cost),
        total_tokens=int(tokens),
        unknown_data_pct=round(100 * no_tokens / total, 1) if total else 0.0,
        confidence=_confidence(db),
        by_application=_dimension(db, AIEvent.application),
        by_model=_dimension(db, AIEvent.model),
        date_range={"start": rng[0], "end": rng[1]},
    )


@router.get("/stats/timeline", response_model=list[TimelinePoint])
def timeline(
    db: Session = Depends(get_db),
    bucket: str = Query("day", pattern="^(day|hour|week)$"),
) -> list[TimelinePoint]:
    trunc = func.date_trunc(bucket, AIEvent.timestamp)
    rows = db.execute(
        select(
            trunc.label("bucket"),
            func.count(),
            func.coalesce(func.sum(AIEvent.estimated_cost), 0),
            func.coalesce(func.sum(_TOKENS), 0),
        )
        .group_by("bucket")
        .order_by("bucket")
    ).all()
    return [
        TimelinePoint(bucket=b, events=n, cost=Decimal(c), tokens=int(t))
        for b, n, c, t in rows
    ]


@router.get("/stats/by-dimension", response_model=list[DimensionCount])
def by_dimension(
    db: Session = Depends(get_db),
    group: str = Query("capability", pattern="^(capability|model|application|project|event_type)$"),
) -> list[DimensionCount]:
    col = getattr(AIEvent, group)
    return _dimension(db, col)


@router.get("/stats/quality", response_model=QualityStats)
def quality(db: Session = Depends(get_db)) -> QualityStats:
    total = db.execute(select(func.count()).select_from(AIEvent)).scalar_one()
    with_tokens = db.execute(
        select(func.count()).where(AIEvent.input_tokens.is_not(None))
    ).scalar_one()
    with_cost = db.execute(
        select(func.count()).where(AIEvent.estimated_cost.is_not(None))
    ).scalar_one()

    # Models that exist but could not be priced (e.g. <synthetic> or unknown).
    unknown_rows = db.execute(
        select(func.distinct(AIEvent.model)).where(AIEvent.estimated_cost.is_(None))
    ).all()
    unknown_models = sorted({r[0] or "unknown" for r in unknown_rows})

    # Count events that had unexpected schema structure during collection.
    drift_count = db.execute(
        select(func.count()).where(
            func.jsonb_array_length(AIEvent.metadata_json["schema_drifts"].as_json()) > 0
        )
    ).scalar_one() or 0

    conf = _confidence(db)
    # Trust score weights confidence tiers.
    weighted = conf.high * 1.0 + conf.medium * 0.5 + conf.low * 0.0
    trust = round(100 * weighted / total, 1) if total else 0.0

    return QualityStats(
        total_events=total,
        with_token_data=with_tokens,
        without_token_data=total - with_tokens,
        with_cost=with_cost,
        without_cost=total - with_cost,
        unknown_models=unknown_models,
        confidence=conf,
        trust_score=trust,
        drift_events=drift_count,
    )
