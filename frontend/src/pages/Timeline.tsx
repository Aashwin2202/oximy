import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { TimelineArea } from "../components/charts/TimelineArea";
import type { TimelinePoint } from "../types";

type Metric = "events" | "tokens" | "cost";

export function Timeline() {
  const [data, setData] = useState<TimelinePoint[]>([]);
  const [metric, setMetric] = useState<Metric>("events");
  const [err, setErr] = useState<string | null>(null);

  const fetch = useCallback(() => {
    api.timeline("day").then(setData).catch((e) => setErr(String(e)));
  }, []);

  useEffect(fetch, [fetch]);
  useAutoRefresh(fetch);

  if (err) return <div className="text-rose-300">Failed to load: {err}</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {(["events", "tokens", "cost"] as Metric[]).map((m) => (
          <button
            key={m}
            onClick={() => setMetric(m)}
            className={`rounded-lg border px-3 py-1 text-sm capitalize ${
              metric === m
                ? "border-blue-400 bg-blue-500/15 text-blue-200"
                : "border-edge text-gray-300"
            }`}
          >
            {m}
          </button>
        ))}
      </div>
      <div className="rounded-xl border border-edge bg-panel p-5">
        <h3 className="mb-2 text-sm font-medium text-gray-300">
          Daily {metric} — real Claude Code activity
        </h3>
        <TimelineArea data={data} metric={metric} />
      </div>
    </div>
  );
}
