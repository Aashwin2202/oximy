import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { StatCard } from "../components/StatCard";
import { ConfidenceDonut } from "../components/charts/ConfidenceDonut";
import { DimensionBar } from "../components/charts/DimensionBar";
import type { OverviewStats } from "../types";

function fmtRange(r: { start: string | null; end: string | null }): string {
  if (!r.start || !r.end) return "";
  const s = new Date(r.start).toLocaleDateString();
  const e = new Date(r.end).toLocaleDateString();
  return `${s} – ${e}`;
}

export function Overview() {
  const [data, setData] = useState<OverviewStats | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const fetch = useCallback(() => {
    api.overview().then(setData).catch((e) => setErr(String(e)));
  }, []);

  useEffect(fetch, [fetch]);
  useAutoRefresh(fetch);

  if (err) return <div className="text-rose-300">Failed to load: {err}</div>;
  if (!data) return <div className="text-gray-400">Loading real usage…</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="AI interactions" value={data.total_events.toLocaleString()} sub={fmtRange(data.date_range)} />
        <StatCard label="Applications" value={String(data.applications)} sub={`${data.tools_used} distinct tools`} />
        <StatCard label="Estimated spend" value={`$${Number(data.estimated_cost).toFixed(2)}`} sub="tokens × model pricing" />
        <StatCard label="Total tokens" value={data.total_tokens.toLocaleString()} sub="incl. cache read/write" />
        <StatCard label="Unknown data" value={`${data.unknown_data_pct}%`} sub="events missing tokens" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-edge bg-panel p-5">
          <h3 className="mb-2 text-sm font-medium text-gray-300">Data confidence</h3>
          <ConfidenceDonut data={data.confidence} />
        </div>
        <div className="rounded-xl border border-edge bg-panel p-5">
          <h3 className="mb-2 text-sm font-medium text-gray-300">Estimated cost by model</h3>
          <DimensionBar data={data.by_model} metric="cost" />
        </div>
      </div>

      <div className="rounded-xl border border-edge bg-panel p-5">
        <h3 className="mb-3 text-sm font-medium text-gray-300">By application</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-gray-400">
            <tr>
              <th className="pb-2">Application</th>
              <th className="pb-2">Interactions</th>
              <th className="pb-2">Tokens</th>
              <th className="pb-2">Est. cost</th>
            </tr>
          </thead>
          <tbody>
            {data.by_application.map((a) => (
              <tr key={a.key} className="border-t border-edge">
                <td className="py-2">{a.key}</td>
                <td className="py-2">{a.events.toLocaleString()}</td>
                <td className="py-2">{a.tokens.toLocaleString()}</td>
                <td className="py-2">${Number(a.cost).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
