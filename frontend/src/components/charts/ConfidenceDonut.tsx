import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ConfidenceBreakdown } from "../../types";

const COLORS = { high: "#34d399", medium: "#fbbf24", low: "#fb7185" };

export function ConfidenceDonut({ data }: { data: ConfidenceBreakdown }) {
  const rows = [
    { name: "high", value: data.high },
    { name: "medium", value: data.medium },
    { name: "low", value: data.low },
  ].filter((r) => r.value > 0);

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={rows} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85}>
          {rows.map((r) => (
            <Cell key={r.name} fill={COLORS[r.name as keyof typeof COLORS]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "#151a23", border: "1px solid #222a36" }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
