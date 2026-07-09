"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BarChart3,
  Gauge,
  Layers,
  RefreshCw,
  Thermometer,
  Wind,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "@/components/providers/auth-provider";
import apiClient from "@/lib/api-client";
import type {
  DashboardKPIs,
  HealthResponse,
  RecentActivityItem,
  ReadinessResponse,
} from "@/types/api";

const ZONE_COLORS: Record<string, string> = {
  CNS: "#6366f1",
  T1: "#22c55e",
  T2: "#10b981",
  RWY: "#f97316",
  BHS: "#a855f7",
  ATC: "#ef4444",
};

const TREND_METRICS = [
  "temperature",
  "humidity",
  "security_wait_time",
  "passenger_count",
  "wind_speed",
  "runway_occupancy",
];

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "healthy" || status === "ready" || status === "configured"
      ? "success"
      : status === "degraded"
        ? "warning"
        : "destructive";
  return <Badge variant={variant}>{status}</Badge>;
}

function KPICard({
  label,
  value,
  unit,
  icon: Icon,
  color = "text-primary",
}: {
  label: string;
  value: number | null | undefined;
  unit?: string;
  icon: React.ElementType;
  color?: string;
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-1 text-3xl font-bold">
              {value != null ? (
                <>
                  {typeof value === "number" ? value.toFixed(1) : value}
                  {unit && (
                    <span className="ml-1 text-base font-normal text-muted-foreground">
                      {unit}
                    </span>
                  )}
                </>
              ) : (
                <span className="text-muted-foreground">—</span>
              )}
            </p>
          </div>
          <div className={`rounded-full bg-muted p-3 ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [trendMetric, setTrendMetric] = useState("temperature");

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>("/health");
      return data;
    },
  });

  const { data: readiness } = useQuery({
    queryKey: ["readiness"],
    queryFn: async () => {
      const { data } = await apiClient.get<ReadinessResponse>("/health/ready");
      return data;
    },
    refetchInterval: 30_000,
  });

  const {
    data: kpis,
    isLoading: kpisLoading,
    refetch: refetchKPIs,
    isFetching,
  } = useQuery<DashboardKPIs>({
    queryKey: ["dashboard-kpis"],
    queryFn: async () => {
      const { data } = await apiClient.get("/dashboard/kpis");
      return data;
    },
    refetchInterval: 60_000,
  });

  const { data: zoneSummary } = useQuery<
    Array<{
      zone_code: string;
      zone_name: string;
      metrics: Record<string, { avg: number; unit: string }>;
    }>
  >({
    queryKey: ["dashboard-zone-summary"],
    queryFn: async () => {
      const { data } = await apiClient.get("/dashboard/zone-summary");
      return data;
    },
    staleTime: 60_000,
  });

  const { data: recentActivity } = useQuery<RecentActivityItem[]>({
    queryKey: ["dashboard-recent-activity"],
    queryFn: async () => {
      const { data } = await apiClient.get("/dashboard/recent-activity?limit=10");
      return data;
    },
    refetchInterval: 30_000,
  });

  const { data: trends } = useQuery<
    Array<{ zone_code: string; zone_name: string; avg_value: number; unit: string }>
  >({
    queryKey: ["dashboard-trends", trendMetric],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/dashboard/trends?metric_name=${trendMetric}`
      );
      return data;
    },
    staleTime: 60_000,
  });

  const chartData =
    trends?.map((t) => ({
      zone: t.zone_code,
      value: t.avg_value,
      unit: t.unit,
    })) ?? [];

  return (
    <AppShell>
      <PageHeader
        title="Dashboard"
        description="Airport operations overview with live KPIs and analytics"
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetchKPIs()}
          disabled={isFetching}
          id="dashboard-refresh-btn"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </PageHeader>

      {/* ── KPI Strip ── */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          label="Total Readings"
          value={kpis?.total_metrics}
          icon={Layers}
        />
        <KPICard
          label="Avg Temperature"
          value={kpis?.avg_temperature}
          unit="°C"
          icon={Thermometer}
          color="text-orange-500"
        />
        <KPICard
          label="Avg Security Wait"
          value={kpis?.avg_security_wait_minutes}
          unit="min"
          icon={Activity}
          color="text-blue-500"
        />
        <KPICard
          label="Flights / Hour"
          value={kpis?.flights_per_hour}
          icon={Wind}
          color="text-emerald-500"
        />
        <KPICard
          label="Runway Occupancy"
          value={kpis?.runway_occupancy_pct}
          unit="%"
          icon={Gauge}
          color="text-red-500"
        />
        <KPICard
          label="Baggage Throughput"
          value={kpis?.baggage_throughput}
          unit="bags/h"
          icon={BarChart3}
          color="text-purple-500"
        />
        <KPICard
          label="System Uptime"
          value={kpis?.system_uptime_pct}
          unit="%"
          icon={Activity}
          color="text-green-500"
        />
        <KPICard
          label="Active Flights"
          value={kpis?.active_flights}
          icon={Wind}
          color="text-indigo-500"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* ── Trend Chart ── */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Zone Metric Comparison</CardTitle>
              <CardDescription>Average values by zone</CardDescription>
            </div>
            <Select value={trendMetric} onValueChange={setTrendMetric}>
              <SelectTrigger className="w-[180px]" id="trend-metric-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TREND_METRICS.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m.replace(/_/g, " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <p className="py-12 text-center text-sm text-muted-foreground">
                No data for selected metric.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="zone" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(val: number, _: string, entry) => [
                      `${val.toFixed(2)} ${entry.payload.unit}`,
                      trendMetric.replace(/_/g, " "),
                    ]}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell
                        key={entry.zone}
                        fill={ZONE_COLORS[entry.zone] ?? "#94a3b8"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* ── Service Status + User ── */}
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Current User</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm">
                <span className="text-muted-foreground">Username: </span>
                <strong>{user?.username ?? "—"}</strong>
              </p>
              <p className="text-sm capitalize">
                <span className="text-muted-foreground">Role: </span>
                <Badge variant="secondary" className="capitalize">
                  {user?.role ?? "—"}
                </Badge>
              </p>
            </CardContent>
          </Card>

          {user?.role === "admin" && (
            <Card>
              <CardHeader>
                <CardTitle>Service Status</CardTitle>
                <CardDescription>Live health checks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Backend API</span>
                  <StatusBadge status={health?.status ?? "unknown"} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Database</span>
                  <StatusBadge status={readiness?.database ?? "unknown"} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Ollama LLM</span>
                  <StatusBadge status={readiness?.ollama ?? "unknown"} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">FAISS Index</span>
                  <StatusBadge status={readiness?.faiss ?? "unknown"} />
                </div>
                {readiness?.metrics_count != null && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Metric rows</span>
                    <span className="text-sm font-medium">
                      {readiness.metrics_count.toLocaleString()}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* ── Zone Summary Table ── */}
      {zoneSummary && zoneSummary.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Zone Overview</CardTitle>
            <CardDescription>
              Average metric values per airport zone
            </CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Zone</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Temp (°C)</TableHead>
                  <TableHead>Humidity (%)</TableHead>
                  <TableHead>Passengers</TableHead>
                  <TableHead>Security Wait</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {zoneSummary.map((zone) => (
                  <TableRow key={zone.zone_code}>
                    <TableCell>
                      <span
                        className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
                        style={{
                          backgroundColor: ZONE_COLORS[zone.zone_code] ?? "#94a3b8",
                        }}
                      >
                        {zone.zone_code}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">{zone.zone_name}</TableCell>
                    <TableCell className="text-sm">
                      {zone.metrics.temperature
                        ? zone.metrics.temperature.avg.toFixed(1)
                        : "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {zone.metrics.humidity
                        ? zone.metrics.humidity.avg.toFixed(1)
                        : "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {zone.metrics.passenger_count
                        ? Math.round(zone.metrics.passenger_count.avg)
                        : "—"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {zone.metrics.security_wait_time
                        ? `${zone.metrics.security_wait_time.avg.toFixed(1)} min`
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* ── Recent Activity ── */}
      {recentActivity && recentActivity.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Last 10 recorded readings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {recentActivity.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-md px-3 py-2 odd:bg-muted/30"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{
                      backgroundColor: ZONE_COLORS[item.zone_code] ?? "#94a3b8",
                    }}
                  />
                  <span className="text-xs font-medium">{item.zone_code}</span>
                  <span className="text-xs text-muted-foreground">
                    {item.metric_name.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="text-xs font-semibold">
                  {item.metric_value} {item.unit}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </AppShell>
  );
}
