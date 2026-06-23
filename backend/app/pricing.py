"""Per-model token pricing and cost computation.

Rates are USD per 1,000,000 tokens, sourced from the Claude API pricing
reference. Cache-write is the 5-minute-TTL rate (1.25x input); cache-read is
0.1x input. There is no precomputed cost in the Claude Code logs, so every
event's cost is derived here from its token counts.
"""

from decimal import Decimal

# Bump this date whenever any rate changes. Stamped on every priced event so
# re-pricing by version is possible without touching historical token counts.
PRICING_VERSION = "2026-06-01"

# input, output, cache_write_5m, cache_read — all per 1M tokens.
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-8": {"input": 5.00, "output": 25.00, "cache_write": 6.25, "cache_read": 0.50},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00, "cache_write": 1.25, "cache_read": 0.10},
}

_MILLION = Decimal(1_000_000)


def resolve_model(model: str | None) -> str | None:
    """Map a raw model id to a pricing key, or None if unknown/synthetic.

    Handles dated suffixes like 'claude-haiku-4-5-20251001' by prefix match.
    """
    if not model or model == "<synthetic>":
        return None
    for key in PRICING:
        if model == key or model.startswith(key):
            return key
    return None


def estimate_cost(
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    cache_read_tokens: int | None = None,
    cache_creation_tokens: int | None = None,
) -> Decimal | None:
    """Return estimated USD cost, or None when the model is unpriceable.

    Cache-read tokens dominate Claude Code usage by volume, so they are priced
    separately rather than folded into the input rate.
    """
    key = resolve_model(model)
    if key is None:
        return None

    rates = PRICING[key]
    total = Decimal(0)
    total += Decimal(input_tokens or 0) / _MILLION * Decimal(str(rates["input"]))
    total += Decimal(output_tokens or 0) / _MILLION * Decimal(str(rates["output"]))
    total += Decimal(cache_read_tokens or 0) / _MILLION * Decimal(str(rates["cache_read"]))
    total += Decimal(cache_creation_tokens or 0) / _MILLION * Decimal(str(rates["cache_write"]))
    return total.quantize(Decimal("0.000001"))
