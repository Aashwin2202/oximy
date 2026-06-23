import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimelinePoint } from "../../types";

export function TimelineArea({
  data,
  metric,
}: {
  data: TimelinePoint[];
  metric: "cost" | "events" | "tokens";
}) {
  const rows = data.map((d) => ({
    bucket: new Date(d.bucket).toLocaleDateString(),
    value: Number(d[metric]),
  }));
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={rows} margin={{ top: 24, left: 10, right: 20, bottom: 0 }}>
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#60a5fa" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#222a36" vertical={false} />
        <XAxis dataKey="bucket" tick={{ fill: "#9aa4b2", fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fill: "#9aa4b2", fontSize: 12 }} domain={[0, "dataMax"]} allowDataOverflow={false} />
        <Tooltip
          contentStyle={{ background: "#151a23", border: "1px solid #222a36" }}
          formatter={(v: number | string) =>
            metric === "cost" ? `$${Number(v).toFixed(2)}` : Number(v).toLocaleString()
          }
        />
        <Area dataKey="value" stroke="#60a5fa" fill="url(#g)" strokeWidth={2} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
