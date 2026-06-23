export function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-edge bg-panel p-5">
      <div className="text-xs uppercase tracking-wide text-gray-400">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
      {sub && <div className="mt-1 text-sm text-gray-400">{sub}</div>}
    </div>
  );
}
