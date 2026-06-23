import { useState } from "react";
import { Overview } from "./pages/Overview";
import { Timeline } from "./pages/Timeline";
import { EventExplorer } from "./pages/EventExplorer";
import { DataQuality } from "./pages/DataQuality";

const TABS = [
  { id: "overview", label: "Overview", el: <Overview /> },
  { id: "timeline", label: "Timeline", el: <Timeline /> },
  { id: "explorer", label: "Event Explorer", el: <EventExplorer /> },
  { id: "quality", label: "Data Quality", el: <DataQuality /> },
] as const;

export default function App() {
  const [tab, setTab] = useState<string>("overview");
  const active = TABS.find((t) => t.id === tab) ?? TABS[0];

  return (
    <div className="min-h-screen">
      <header className="border-b border-edge bg-panel">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <h1 className="text-lg font-semibold">AI Usage Intelligence</h1>
          <p className="text-xs text-gray-400">
            Unified view of real AI tool usage — what's used, how much it costs, and
            how trustworthy the data is.
          </p>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 px-6">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm ${
                tab === t.id
                  ? "border-blue-400 text-white"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-6">{active.el}</main>
    </div>
  );
}
