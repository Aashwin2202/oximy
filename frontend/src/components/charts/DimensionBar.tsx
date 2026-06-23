import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DimensionCount } from "../../types";

export function DimensionBar({
  data,
  metric,
}: {
  data: DimensionCount[];
  metric: "cost" | "events" | "tokens";
}) {
  const rows = data.map((d) => ({ key: d.key, value: d[metric] }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={rows} margin={{ left: 10, right: 10 }}>
        <CartesianGrid stroke="#222a36" vertical={false} />
        <XAxis dataKey="key" tick={{ fill: "#9aa4b2", fontSize: 12 }} />
        <YAxis tick={{ fill: "#9aa4b2", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ background: "#151a23", border: "1px solid #222a36" }}
          formatter={(v: number | string) =>
            metric === "cost" ? `$${Number(v).toFixed(2)}` : Number(v).toLocaleString()
          }
        />
        <Bar dataKey="value" fill="#60a5fa" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
