import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LineageView } from "../types";

function Stage({ title, body }: { title: string; body: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-blue-300">{title}</div>
      <div className="mt-1 rounded-lg border border-edge bg-ink p-3 text-xs text-gray-300">
        {body}
      </div>
      <div className="my-1 text-center text-gray-500">↓</div>
    </div>
  );
}

function KV({ k, v, dim }: { k: string; v: React.ReactNode; dim?: boolean }) {
  return (
    <div className="flex gap-2">
      <span className="w-36 shrink-0 text-gray-500">{k}</span>
      <span className={dim ? "text-gray-500 italic" : "break-all"}>{v}</span>
    </div>
  );
}

export function LineageDrawer({ id, onClose }: { id: string; onClose: () => void }) {
  const [data, setData] = useState<LineageView | null>(null);

  useEffect(() => {
    api.lineage(id).then(setData).catch(() => setData(null));
  }, [id]);

  const raw = data?.raw_source as Record<string, unknown> | undefined;

  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-md overflow-y-auto border-l border-edge bg-panel p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-medium">Event lineage</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        {!data ? (
          <div className="text-gray-400">Loading…</div>
        ) : (
          <div className="space-y-2">
            <Stage
              title="Raw source"
              body={
                <div className="space-y-1">
                  <KV k="source" v={String(raw?.source ?? "")} />
                  <KV k="raw_line_sha256" v={<span className="font-mono text-[10px]">{String(raw?.raw_line_sha256 ?? "—")}</span>} />
                  <KV k="session_id" v={String(raw?.session_id ?? "—")} />
                  <KV k="collector_run_id" v={<span className="font-mono text-[10px]">{String(raw?.collector_run_id ?? "—")}</span>} />
                  <KV k="collected_at" v={raw?.collected_at ? new Date(String(raw.collected_at)).toLocaleString() : "—"} />
                  <div className="mt-2 border-t border-edge pt-2">
                    <div className="mb-1 text-gray-500">Identity</div>
                    <KV k="user" v={String(raw?.user ?? "local")} />
                    <KV
                      k="identity_status"
                      v={
                        <span className={raw?.identity_status === "unresolved" ? "text-amber-400" : "text-emerald-400"}>
                          {String(raw?.identity_status ?? "unknown")}
                        </span>
                      }
                    />
                    <KV k="note" v={String(raw?.identity_note ?? "")} dim />
                  </div>
                  {Array.isArray(raw?.schema_drifts) && (raw.schema_drifts as string[]).length > 0 && (
                    <div className="mt-2 border-t border-edge pt-2">
                      <div className="text-rose-400">Schema drifts detected</div>
                      {(raw.schema_drifts as string[]).map((d) => (
                        <div key={d} className="text-rose-300">• {d}</div>
                      ))}
                    </div>
                  )}
                  <KV k="privacy" v="Prompt text never stored — hash only" dim />
                </div>
              }
            />
            <Stage
              title="Parser"
              body={<pre className="whitespace-pre-wrap">{JSON.stringify(data.parser, null, 2)}</pre>}
            />
            <Stage
              title="Canonical event"
              body={
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(
                    {
                      id: data.canonical_event.id,
                      application: data.canonical_event.application,
                      model: data.canonical_event.model,
                      capability: data.canonical_event.capability,
                      tokens:
                        (data.canonical_event.input_tokens ?? 0) +
                        (data.canonical_event.output_tokens ?? 0),
                      estimated_cost: data.canonical_event.estimated_cost,
                      confidence: data.canonical_event.confidence,
                    },
                    null,
                    2,
                  )}
                </pre>
              }
            />
            <div className="text-xs font-semibold uppercase tracking-wide text-blue-300">
              Feeds metrics
            </div>
            <ul className="list-disc rounded-lg border border-edge bg-ink p-3 pl-7 text-xs text-gray-300">
              {data.feeds_metrics.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
