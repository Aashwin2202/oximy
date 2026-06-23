import type { Confidence } from "../types";

const STYLES: Record<Confidence, string> = {
  high: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  low: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${STYLES[confidence]}`}
    >
      {confidence}
    </span>
  );
}
