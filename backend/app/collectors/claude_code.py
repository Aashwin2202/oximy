"""Claude Code collector.

Walks ``~/.claude/projects/*/*.jsonl`` and turns assistant turns into canonical
AI events. The one subtle correctness point: many streamed lines share a single
``message.id`` and repeat *identical* usage. We dedup by ``message.id`` and take
usage exactly once — summing would inflate cost by ~2.4x on this machine.

Privacy: prompt/response text is never persisted. We keep token counts, tool
names, and a sha256 of the raw line for lineage.
"""

import glob
import hashlib
import json
import logging
import os
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone

log = logging.getLogger(__name__)

from app.collectors.base import (
    capability_for_tools,
    event_type_for_tools,
    finalize_cost_and_confidence,
)
from app.pricing import resolve_model

APPLICATION = "Claude Code"
PROVIDER = "anthropic"
SOURCE = "claude_code"


def _project_from(cwd: str | None, file_path: str) -> str:
    if cwd:
        return os.path.basename(cwd.rstrip("/")) or cwd
    # Fallback: dir name like "-Users-winaash-Desktop-Projects-oximy"
    return os.path.basename(os.path.dirname(file_path)).split("-")[-1]


def iter_canonical_events(claude_dir: str) -> Iterator[dict]:
    """Yield one canonical-event dict per unique assistant message.id.

    Grouping is global across all files: a single message.id can recur across
    JSONL files when a session is resumed or branched, so per-file grouping
    would emit duplicates and double-count cost.
    """
    run_id = str(uuid.uuid4())
    run_ts = datetime.now(timezone.utc).isoformat()

    pattern = os.path.join(claude_dir, "projects", "*", "*.jsonl")
    files = sorted(glob.glob(pattern))
    groups: dict[str, dict] = {}
    order: list[str] = []
    counters: dict[str, int] = {"lines": 0, "json_errors": 0, "skipped_no_id": 0, "drift": 0}
    for file_path in files:
        _accumulate_file(file_path, groups, order, counters)

    emitted = 0
    for mid in order:
        event = _build_event(groups[mid], run_id, run_ts)
        if event is not None:
            emitted += 1
            yield event

    log.info(
        "collector run=%s files=%d lines=%d json_errors=%d skipped_no_id=%d unique_events=%d drift=%d",
        run_id[:8],
        len(files),
        counters["lines"],
        counters["json_errors"],
        counters["skipped_no_id"],
        emitted,
        counters["drift"],
    )


def _accumulate_file(
    file_path: str,
    groups: dict[str, dict],
    order: list[str],
    counters: dict[str, int],
) -> None:
    with open(file_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            counters["lines"] += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                counters["json_errors"] += 1
                log.debug("json_error: file=%s", file_path)
                continue
            if obj.get("type") != "assistant":
                continue

            msg = obj.get("message", {})
            mid = msg.get("id") or obj.get("requestId")
            if not mid:
                counters["skipped_no_id"] += 1
                continue

            tools = [
                b.get("name")
                for b in msg.get("content", [])
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name")
            ]

            if mid not in groups:
                order.append(mid)
                usage = msg.get("usage", {}) or {}
                model = msg.get("model")

                # Drift detection: flag structural surprises on first occurrence.
                drifts: list[str] = []
                if not obj.get("timestamp"):
                    drifts.append("no_timestamp")
                if model and resolve_model(model) and not usage:
                    drifts.append("no_usage_block")
                elif usage and all(
                    usage.get(k) is None
                    for k in ("input_tokens", "output_tokens",
                              "cache_read_input_tokens", "cache_creation_input_tokens")
                ):
                    drifts.append("empty_usage")

                if drifts:
                    counters["drift"] += 1
                    log.warning("schema_drift: mid=%s drifts=%s file=%s", mid, drifts, file_path)

                groups[mid] = {
                    "message_id": mid,
                    "timestamp": obj.get("timestamp"),
                    "model": model,
                    "cwd": obj.get("cwd"),
                    "file_path": file_path,
                    "session_id": obj.get("sessionId"),
                    "git_branch": obj.get("gitBranch"),
                    "version": obj.get("version"),
                    # Usage taken ONCE — repeated identically across streamed lines.
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "cache_read_tokens": usage.get("cache_read_input_tokens"),
                    "cache_creation_tokens": usage.get("cache_creation_input_tokens"),
                    "tools": set(tools),
                    "raw_hash": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                    "schema_drifts": drifts,
                }
            else:
                groups[mid]["tools"].update(tools)
                # Keep the earliest timestamp.
                ts = obj.get("timestamp")
                if ts and (groups[mid]["timestamp"] is None or ts < groups[mid]["timestamp"]):
                    groups[mid]["timestamp"] = ts


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Claude Code writes ISO-8601 with a trailing 'Z'.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_event(g: dict, run_id: str, run_ts: str) -> dict | None:
    ts = _parse_ts(g["timestamp"])
    if ts is None:
        return None
    mid = g["message_id"]
    tools = sorted(g["tools"])
    event = {
        "id": f"{SOURCE}:{mid}",
        "timestamp": ts,
        "application": APPLICATION,
        "provider": PROVIDER,
        "model": g["model"],
        "event_type": event_type_for_tools(tools),
        "capability": capability_for_tools(tools),
        "input_tokens": g["input_tokens"],
        "output_tokens": g["output_tokens"],
        "cache_read_tokens": g["cache_read_tokens"],
        "cache_creation_tokens": g["cache_creation_tokens"],
        "estimated_cost": None,
        "project": _project_from(g["cwd"], g["file_path"]),
        "confidence": None,
        "metadata_json": {
            "tools": tools,
            "session_id": g["session_id"],
            "git_branch": g["git_branch"],
            "version": g["version"],
            "raw_hash": g["raw_hash"],
            "schema_drifts": g["schema_drifts"],
            "collector_run_id": run_id,
            "collected_at": run_ts,
            "user": "local",
            "identity_status": "unresolved",
            "identity_note": "device-local session; no authoritative user ID available",
        },
    }
    return finalize_cost_and_confidence(event)
