import type {
  EventPage,
  LineageView,
  OverviewStats,
  QualityStats,
  TimelinePoint,
  DimensionCount,
} from "../types";

// In dev, Vite proxies /api -> backend. In production (Vercel), set
// VITE_API_URL to the deployed backend origin.
const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  overview: () => get<OverviewStats>("/stats/overview"),
  timeline: (bucket = "day") => get<TimelinePoint[]>(`/stats/timeline?bucket=${bucket}`),
  byDimension: (group: string) => get<DimensionCount[]>(`/stats/by-dimension?group=${group}`),
  quality: () => get<QualityStats>("/stats/quality"),
  events: (query: string) => get<EventPage>(`/events${query}`),
  lineage: (id: string) => get<LineageView>(`/events/${encodeURIComponent(id)}/lineage`),
};
