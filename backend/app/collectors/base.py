"""Shared canonical-event construction used by all collectors."""

from app.pricing import PRICING_VERSION, estimate_cost, resolve_model

# Map a Claude Code tool name to a capability. Highest-signal wins when an
# event used several tools (see CAPABILITY_PRIORITY).
TOOL_CAPABILITY: dict[str, str] = {
    "Read": "file_read",
    "Edit": "file_edit",
    "Write": "file_edit",
    "Bash": "shell",
    "Agent": "subagent",
    "Task": "subagent",
    "WebFetch": "search",
    "WebSearch": "search",
    "ToolSearch": "search",
    "Grep": "file_read",
    "Glob": "file_read",
    "TodoWrite": "planning",
    "ExitPlanMode": "planning",
    "AskUserQuestion": "planning",
}

# Lower index = higher signal. The capability shown is the most meaningful
# action in the turn, not just the first tool seen.
CAPABILITY_PRIORITY = [
    "subagent",
    "file_edit",
    "shell",
    "search",
    "mcp",
    "file_read",
    "planning",
    "chat",
]


def capability_for_tools(tools: list[str]) -> str:
    caps = set()
    for t in tools:
        if t.startswith("mcp__"):
            caps.add("mcp")
        else:
            caps.add(TOOL_CAPABILITY.get(t, "chat"))
    for cap in CAPABILITY_PRIORITY:
        if cap in caps:
            return cap
    return "chat"


def event_type_for_tools(tools: list[str]) -> str:
    if any(t in ("Agent", "Task") for t in tools):
        return "agent_run"
    if any(t in ("WebFetch", "WebSearch") for t in tools):
        return "web_search"
    if tools:
        return "tool_call"
    return "message"


def derive_confidence(model: str | None, has_full_usage: bool) -> str:
    """high = priced model + full usage; low = synthetic/unpriceable;
    medium = known model but missing usage."""
    if not model or model == "<synthetic>" or resolve_model(model) is None:
        return "low"
    return "high" if has_full_usage else "medium"


def finalize_cost_and_confidence(event: dict) -> dict:
    """Fill estimated_cost (if absent) and confidence on a canonical-event dict.

    Synthetic/unpriceable events get null tokens and cost so they never inflate
    spend — the platform shows them as low-confidence instead.
    """
    model = event.get("model")
    if resolve_model(model) is None:
        # Unpriceable: scrub token/cost so dashboards stay honest.
        event["input_tokens"] = None
        event["output_tokens"] = None
        event["cache_read_tokens"] = None
        event["cache_creation_tokens"] = None
        event["estimated_cost"] = None
        event["confidence"] = "low"
        return event

    has_full_usage = (
        event.get("input_tokens") is not None and event.get("output_tokens") is not None
    )
    if event.get("estimated_cost") is None:
        event["estimated_cost"] = estimate_cost(
            model,
            event.get("input_tokens"),
            event.get("output_tokens"),
            event.get("cache_read_tokens"),
            event.get("cache_creation_tokens"),
        )
        # Stamp the rate-table version so a future pricing change is a
        # reprice-by-version job, not a silent overwrite of history.
        if event.get("estimated_cost") is not None:
            meta = event.setdefault("metadata_json", {})
            meta["pricing_version"] = PRICING_VERSION
    if not event.get("confidence"):
        event["confidence"] = derive_confidence(model, has_full_usage)
    return event
