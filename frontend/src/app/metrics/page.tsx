"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Filter,
  RefreshCw,
  Search,
} from "lucide-react";
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
import { Input } from "@/components/ui/input";
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
import apiClient from "@/lib/api-client";
import type {
  MetricItem,
  MetricListResponse,
  MetricSummaryResponse,
} from "@/types/api";

const ZONE_COLOR: Record<string, string> = {
  CNS: "bg-blue-100 text-blue-800",
  T1: "bg-green-100 text-green-800",
  T2: "bg-emerald-100 text-emerald-800",
  RWY: "bg-orange-100 text-orange-800",
  BHS: "bg-purple-100 text-purple-800",
  ATC: "bg-red-100 text-red-800",
};

function ZoneBadge({ code }: { code: string }) {
  const cls = ZONE_COLOR[code] ?? "bg-gray-100 text-gray-800";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}
    >
      {code}
    </span>
  );
}

function formatValue(value: number, unit: string): string {
  const rounded = Math.round(value * 100) / 100;
  return `${rounded} ${unit}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function MetricsPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [zoneFilter, setZoneFilter] = useState<string>("all");
  const [metricFilter, setMetricFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sortBy, setSortBy] = useState("recorded_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Summary for filter dropdowns
  const { data: summary } = useQuery<MetricSummaryResponse>({
    queryKey: ["metrics-summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<MetricSummaryResponse>("/metrics/summary");
      return data;
    },
    staleTime: 60_000,
  });

  // Main metrics list
  const {
    data: metrics,
    isLoading,
    isFetching,
    refetch,
  } = useQuery<MetricListResponse>({
    queryKey: [
      "metrics",
      page,
      pageSize,
      zoneFilter,
      metricFilter,
      debouncedSearch,
      sortBy,
      sortOrder,
    ],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      if (zoneFilter && zoneFilter !== "all") params.set("zone_code", zoneFilter);
      if (metricFilter && metricFilter !== "all") params.set("metric_name", metricFilter);
      if (debouncedSearch) params.set("search", debouncedSearch);
      params.set("sort_by", sortBy);
      params.set("sort_order", sortOrder);
      const { data } = await apiClient.get<MetricListResponse>(`/metrics?${params}`);
      return data;
    },
    staleTime: 30_000,
  });

  const handleSearch = (value: string) => {
    setSearch(value);
    clearTimeout((window as unknown as Record<string, ReturnType<typeof setTimeout>>)._searchTimer);
    (window as unknown as Record<string, ReturnType<typeof setTimeout>>)._searchTimer = setTimeout(() => {
      setDebouncedSearch(value);
      setPage(1);
    }, 400);
  };

  const handleFilterChange = () => setPage(1);

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortBy !== col) return <span className="ml-1 text-muted-foreground/40">↕</span>;
    return <span className="ml-1">{sortOrder === "asc" ? "↑" : "↓"}</span>;
  };

  return (
    <AppShell>
      <PageHeader
        title="Operational Metrics"
        description="Airport zone sensor readings with filtering, sorting, and pagination"
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          id="metrics-refresh-btn"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </PageHeader>

      {/* Summary KPI strip */}
      {summary && (
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-1 pt-4">
              <CardDescription className="text-xs">Total Readings</CardDescription>
              <CardTitle className="text-2xl">{summary.total_metrics.toLocaleString()}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-1 pt-4">
              <CardDescription className="text-xs">Active Zones</CardDescription>
              <CardTitle className="text-2xl">{summary.zones.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-1 pt-4">
              <CardDescription className="text-xs">Metric Types</CardDescription>
              <CardTitle className="text-2xl">{summary.metric_types.length}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filter &amp; Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {/* Search */}
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="metrics-search"
                placeholder="Search zones, metrics..."
                className="pl-9"
                value={search}
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>

            {/* Zone filter */}
            <Select
              value={zoneFilter}
              onValueChange={(v) => {
                setZoneFilter(v);
                handleFilterChange();
              }}
            >
              <SelectTrigger id="metrics-zone-filter" className="w-[160px]">
                <SelectValue placeholder="All Zones" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Zones</SelectItem>
                {summary?.zones.map((z) => (
                  <SelectItem key={z} value={z}>
                    {z}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Metric type filter */}
            <Select
              value={metricFilter}
              onValueChange={(v) => {
                setMetricFilter(v);
                handleFilterChange();
              }}
            >
              <SelectTrigger id="metrics-type-filter" className="w-[200px]">
                <SelectValue placeholder="All Metric Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Metric Types</SelectItem>
                {summary?.metric_types.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m.replace(/_/g, " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Page size */}
            <Select
              value={String(pageSize)}
              onValueChange={(v) => {
                setPageSize(Number(v));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[110px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 50, 100].map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    {n} / page
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Metrics table */}
      <Card className="mt-4">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-48 items-center justify-center">
              <p className="text-sm text-muted-foreground animate-pulse">Loading metrics…</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort("zone_code")}
                    >
                      Zone <SortIcon col="zone_code" />
                    </TableHead>
                    <TableHead>Zone Name</TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort("metric_name")}
                    >
                      Metric <SortIcon col="metric_name" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none text-right"
                      onClick={() => toggleSort("metric_value")}
                    >
                      Value <SortIcon col="metric_value" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort("recorded_at")}
                    >
                      Recorded <SortIcon col="recorded_at" />
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {metrics?.items.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-12 text-center text-muted-foreground">
                        No metrics match your filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    metrics?.items.map((item: MetricItem) => (
                      <TableRow key={item.id} className="hover:bg-muted/50">
                        <TableCell>
                          <ZoneBadge code={item.zone_code} />
                        </TableCell>
                        <TableCell className="text-sm">{item.zone_name}</TableCell>
                        <TableCell>
                          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                            {item.metric_name.replace(/_/g, " ")}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatValue(item.metric_value, item.unit)}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(item.recorded_at)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {metrics && metrics.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * pageSize + 1}–
            {Math.min(page * pageSize, metrics.total)} of {metrics.total} records
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              disabled={page === 1}
              onClick={() => setPage(1)}
              id="metrics-first-page"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              id="metrics-prev-page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="px-3 text-sm">
              {page} / {metrics.total_pages}
            </span>
            <Button
              variant="outline"
              size="icon"
              disabled={page === metrics.total_pages}
              onClick={() => setPage((p) => p + 1)}
              id="metrics-next-page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              disabled={page === metrics.total_pages}
              onClick={() => setPage(metrics.total_pages)}
              id="metrics-last-page"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </AppShell>
  );
}
