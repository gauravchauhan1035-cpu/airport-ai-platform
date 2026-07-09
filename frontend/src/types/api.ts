export type UserRole = "admin" | "analyst" | "viewer";

export interface User {
  id: number;
  username: string;
  role: UserRole;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
  metrics_count: number;
  ollama: string;
  faiss: string;
}

export interface AskRequest {
  question: string;
  session_id?: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  route: "SQL" | "RAG" | "BOTH";
  execution_time_ms: number;
  sql?: string;
  sql_rows?: Record<string, unknown>[];
  row_count?: number;
  retrieved_chunks?: Array<{
    document_name: string;
    page_number: number;
    content: string;
    score: number;
  }>;
}

// ── Metrics ──────────────────────────────────────────────────────────────────

export interface MetricItem {
  id: number;
  zone_code: string;
  zone_name: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  recorded_at: string;
  created_at: string;
}

export interface MetricListResponse {
  items: MetricItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MetricSummaryResponse {
  total_metrics: number;
  zones: string[];
  metric_types: string[];
}

// ── Documents ─────────────────────────────────────────────────────────────────

export interface DocumentItem {
  id: number;
  filename: string;
  original_name: string;
  document_type: string;
  version: number;
  status: "ACTIVE" | "ARCHIVED" | "DELETED";
  page_count: number;
  chunk_count: number;
  embedding_model?: string;
  file_path?: string;
  created_by?: string;
  last_indexed?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}

export interface SearchResult {
  document_name: string;
  page_number: number;
  content: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  execution_time_ms: number;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface DashboardKPIs {
  total_metrics: number;
  total_zones: number;
  avg_temperature: number | null;
  avg_security_wait_minutes: number | null;
  flights_per_hour: number | null;
  runway_occupancy_pct: number | null;
  baggage_throughput: number | null;
  system_uptime_pct: number | null;
  active_flights: number | null;
  avg_humidity: number | null;
}

export interface ZoneSummaryItem {
  zone_code: string;
  zone_name: string;
  metrics: Record<string, number>;
}

export interface RecentActivityItem {
  id: number;
  zone_code: string;
  zone_name: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  recorded_at: string;
}

export interface TrendPoint {
  bucket: string;
  zone_code: string;
  metric_name: string;
  avg_value: number;
}
