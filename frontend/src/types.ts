export type Confidence = "high" | "medium" | "low";

export interface AIEvent {
  id: string;
  timestamp: string;
  application: string;
  provider: string;
  model: string | null;
  event_type: string;
  capability: string;
  input_tokens: number | null;
  output_tokens: number | null;
  cache_read_tokens: number | null;
  cache_creation_tokens: number | null;
  estimated_cost: number | null;
  project: string | null;
  confidence: Confidence;
  metadata_json: {
    tools?: string[];
    session_id?: string | null;
    git_branch?: string | null;
    version?: string | null;
    raw_hash?: string | null;
    schema_drifts?: string[];
    collector_run_id?: string;
    collected_at?: string;
    user?: string | null;
    identity_status?: string;
    identity_note?: string;
  };
}

export interface EventPage {
  items: AIEvent[];
  next_cursor: string | null;
}

export interface ConfidenceBreakdown {
  high: number;
  medium: number;
  low: number;
}

export interface DimensionCount {
  key: string;
  events: number;
  cost: number;
  tokens: number;
}

export interface OverviewStats {
  total_events: number;
  applications: number;
  tools_used: number;
  estimated_cost: number;
  total_tokens: number;
  unknown_data_pct: number;
  confidence: ConfidenceBreakdown;
  by_application: DimensionCount[];
  by_model: DimensionCount[];
  date_range: { start: string | null; end: string | null };
}

export interface TimelinePoint {
  bucket: string;
  events: number;
  cost: number;
  tokens: number;
}

export interface QualityStats {
  total_events: number;
  with_token_data: number;
  without_token_data: number;
  with_cost: number;
  without_cost: number;
  unknown_models: string[];
  confidence: ConfidenceBreakdown;
  trust_score: number;
  drift_events: number;
}

export interface LineageView {
  raw_source: Record<string, unknown>;
  parser: Record<string, unknown>;
  canonical_event: AIEvent;
  feeds_metrics: string[];
}
