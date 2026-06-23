import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { LineageDrawer } from "../components/LineageDrawer";
import type { AIEvent } from "../types";

const CAPABILITIES = [
  "",
  "file_edit",
  "file_read",
  "shell",
  "search",
  "subagent",
  "planning",
  "mcp",
  "chat",
];

export function EventExplorer() {
  const [items, setItems] = useState<AIEvent[]>([]);
  const [capability, setCapability] = useState("");
  const [confidence, setConfidence] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const fetchEvents = useCallback(() => {
    const params = new URLSearchParams();
    if (capability) params.set("capability", capability);
    if (confidence) params.set("confidence", confidence);
    params.set("limit", "100");
    api
      .events(`?${params.toString()}`)
      .then((p) => setItems(p.items))
      .catch((e) => setErr(String(e)));
  }, [capability, confidence]);

  useEffect(fetchEvents, [fetchEvents]);
  useAutoRefresh(fetchEvents);

  if (err) return <div className="text-rose-300">Failed to load: {err}</div>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <select
          value={capability}
          onChange={(e) => setCapability(e.target.value)}
          className="rounded-lg border border-edge bg-panel px-3 py-1 text-sm"
        >
          {CAPABILITIES.map((c) => (
            <option key={c} value={c}>
              {c || "all capabilities"}
            </option>
          ))}
        </select>
        <select
          value={confidence}
          onChange={(e) => setConfidence(e.target.value)}
          className="rounded-lg border border-edge bg-panel px-3 py-1 text-sm"
        >
          {["", "high", "medium", "low"].map((c) => (
            <option key={c} value={c}>
              {c || "all confidence"}
            </option>
          ))}
        </select>
        <span className="self-center text-sm text-gray-400">
          {items.length} events (click a row for lineage)
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-edge bg-panel">
        <table className="w-full text-sm">
          <thead className="text-left text-gray-400">
            <tr>
              <th className="p-3">Time</th>
              <th className="p-3">App</th>
              <th className="p-3">Model</th>
              <th className="p-3">Capability</th>
              <th className="p-3">Tokens</th>
              <th className="p-3">Cost</th>
              <th className="p-3">User</th>
              <th className="p-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr
                key={e.id}
                onClick={() => setSelected(e.id)}
                className="cursor-pointer border-t border-edge hover:bg-ink"
              >
                <td className="p-3 text-gray-400">{new Date(e.timestamp).toLocaleString()}</td>
                <td className="p-3">{e.application}</td>
                <td className="p-3">{e.model ?? "—"}</td>
                <td className="p-3">{e.capability}</td>
                <td className="p-3">
                  {((e.input_tokens ?? 0) + (e.output_tokens ?? 0)).toLocaleString()}
                </td>
                <td className="p-3">{e.estimated_cost != null ? `$${Number(e.estimated_cost).toFixed(4)}` : "—"}</td>
                <td className="p-3 text-gray-500 italic text-xs">{e.metadata_json?.user ?? "local"}</td>
                <td className="p-3">
                  <ConfidenceBadge confidence={e.confidence} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && <LineageDrawer id={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
