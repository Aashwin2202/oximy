import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { StatCard } from "../components/StatCard";
import type { QualityStats } from "../types";

function Bar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total ? Math.round((100 * value) / total) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="text-gray-400">
          {value.toLocaleString()} ({pct}%)
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-ink">
        <div className="h-2 rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export function DataQuality() {
  const [data, setData] = useState<QualityStats | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const fetch = useCallback(() => {
    api.quality().then(setData).catch((e) => setErr(String(e)));
  }, []);

  useEffect(fetch, [fetch]);
  useAutoRefresh(fetch);

  if (err) return <div className="text-rose-300">Failed to load: {err}</div>;
  if (!data) return <div className="text-gray-400">Loading…</div>;

  return (
    <div className="space-y-6">
      <p className="max-w-2xl text-sm text-gray-400">
        How trustworthy is this AI usage data? Claude Code reports exact tokens, so
        those events are high-confidence. Sources without token data (and synthetic
        local events) are surfaced honestly rather than guessed.
      </p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Trust score" value={`${data.trust_score}%`} sub="confidence-weighted" />
        <StatCard label="Events with tokens" value={`${data.with_token_data}/${data.total_events}`} />
        <StatCard label="Events with cost" value={`${data.with_cost}/${data.total_events}`} />
        <div className="rounded-xl border border-edge bg-panel p-4">
          <div className="text-xs text-gray-400">Schema drifts</div>
          <div className={`mt-1 text-2xl font-semibold ${data.drift_events > 0 ? "text-amber-400" : "text-emerald-400"}`}>
            {data.drift_events}
          </div>
          <div className="mt-1 text-xs text-gray-500">
            {data.drift_events === 0 ? "No structural surprises" : "events with unexpected structure"}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-edge bg-panel p-5 space-y-4">
        <h3 className="text-sm font-medium text-gray-300">Coverage</h3>
        <Bar label="Token data present" value={data.with_token_data} total={data.total_events} color="#34d399" />
        <Bar label="Cost computed" value={data.with_cost} total={data.total_events} color="#60a5fa" />
        <Bar label="Missing token data" value={data.without_token_data} total={data.total_events} color="#fb7185" />
      </div>

      <div className="rounded-xl border border-edge bg-panel p-5">
        <h3 className="mb-2 text-sm font-medium text-gray-300">Models that could not be priced</h3>
        {data.unknown_models.length === 0 ? (
          <div className="text-sm text-gray-400">None — every model mapped to a price.</div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {data.unknown_models.map((m) => (
              <span key={m} className="rounded-full border border-rose-500/30 bg-rose-500/15 px-2 py-0.5 text-xs text-rose-300">
                {m}
              </span>
            ))}
          </div>
        )}
        <p className="mt-3 text-xs text-gray-500">
          Costs are <span className="text-gray-300">estimated</span> from token counts ×
          published per-model pricing, not from billing. Estimated, not actual.
        </p>
      </div>
    </div>
  );
}
