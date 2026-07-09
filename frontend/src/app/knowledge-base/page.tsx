"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Search,
  Upload,
  X,
  MoreHorizontal,
  RefreshCw,
  Archive,
  Trash2,
  Eye,
  FileUp
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/components/providers/auth-provider";
import apiClient from "@/lib/api-client";
import type { DocumentItem, DocumentListResponse, SearchResponse } from "@/types/api";

function formatDate(iso: string | undefined): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export default function KnowledgeBasePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  
  const [replaceTargetId, setReplaceTargetId] = useState<number | null>(null);

  const canManage = user?.role === "admin"; // Only Admin manages KB

  // ── Fetch document list ────────────────────────────────────────────────────
  const { data: docList, isLoading } = useQuery<DocumentListResponse>({
    queryKey: ["documents"],
    queryFn: async () => {
      const { data } = await apiClient.get<DocumentListResponse>("/documents");
      return data;
    },
  });

  // ── Upload mutation ────────────────────────────────────────────────────────
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) setUploadProgress(Math.round((e.loaded * 100) / e.total));
        },
      });
      return data;
    },
    onSuccess: () => {
      setUploadProgress(null);
      setUploadError("");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setUploadError(axiosErr.response?.data?.detail ?? "Upload failed.");
      setUploadProgress(null);
    },
  });

  // ── Replace mutation ───────────────────────────────────────────────────────
  const replaceMutation = useMutation({
    mutationFn: async ({ id, file }: { id: number; file: File }) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.put(`/documents/${id}/replace`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      setReplaceTargetId(null);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  // ── Re-index mutation ──────────────────────────────────────────────────────
  const reindexMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.post(`/documents/${id}/reindex`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  // ── Archive mutation ───────────────────────────────────────────────────────
  const archiveMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.post(`/documents/${id}/archive`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  // ── Delete mutation ────────────────────────────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/documents/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadError("");
      uploadMutation.mutate(file);
    }
    e.target.value = "";
  };

  const handleReplaceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && replaceTargetId) {
      if (confirm(`Are you sure you want to replace this document? This will archive the old version.`)) {
        replaceMutation.mutate({ id: replaceTargetId, file });
      } else {
        setReplaceTargetId(null);
      }
    }
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setUploadError("");
      uploadMutation.mutate(file);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const { data } = await apiClient.post<SearchResponse>("/documents/search", {
        query: searchQuery,
        top_k: 5,
      });
      setSearchResults(data);
    } catch {
      setSearchResults(null);
    } finally {
      setIsSearching(false);
    }
  };

  const triggerReplace = (id: number) => {
    setReplaceTargetId(id);
    replaceInputRef.current?.click();
  };

  return (
    <AppShell>
      <PageHeader
        title="Knowledge Base"
        description="Enterprise Knowledge Base Management: Upload, version, and manage RAG documents."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* ── Left: Upload + Document list ── */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Upload zone */}
          {canManage && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-4 w-4" />
                  Upload Document
                </CardTitle>
                <CardDescription>
                  Upload PDFs to be versioned and indexed into the active knowledge base.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className={`flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
                    dragOver
                      ? "border-primary bg-primary/5"
                      : "border-muted-foreground/25 hover:border-primary/50"
                  }`}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                >
                  <FileText className="h-12 w-12 text-muted-foreground/40" />
                  <div>
                    <p className="text-sm font-medium">Drag & drop a PDF here</p>
                    <p className="mt-1 text-xs text-muted-foreground">or click to browse</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadMutation.isPending}
                    id="upload-browse-btn"
                  >
                    {uploadMutation.isPending ? "Uploading…" : "Browse files"}
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf"
                    className="hidden"
                    onChange={handleFileChange}
                    id="document-file-input"
                  />
                  
                  {/* Hidden input for replace workflow */}
                  <input
                    ref={replaceInputRef}
                    type="file"
                    accept="application/pdf"
                    className="hidden"
                    onChange={handleReplaceChange}
                  />
                </div>

                {uploadProgress !== null && (
                  <div className="mt-4">
                    <div className="mb-1 flex justify-between text-xs text-muted-foreground">
                      <span>Uploading…</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-primary transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {uploadError && (
                  <div className="mt-3 flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    <X className="h-4 w-4 flex-shrink-0" />
                    {uploadError}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Document list */}
          <Card>
            <CardHeader>
              <CardTitle>Enterprise Knowledge Base</CardTitle>
              <CardDescription>
                {docList?.total ?? 0} document(s) in the system
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? (
                <p className="py-12 text-center text-sm text-muted-foreground animate-pulse">
                  Loading…
                </p>
              ) : !docList?.items.length ? (
                <p className="py-12 text-center text-sm text-muted-foreground">
                  No documents found.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-center">Chunks</TableHead>
                      <TableHead className="text-center">Version</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Indexed</TableHead>
                      {canManage && <TableHead className="text-right">Actions</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {docList.items.map((doc: DocumentItem) => (
                      <TableRow key={doc.id} className={doc.status !== "ACTIVE" ? "opacity-60" : ""}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium max-w-[200px] truncate">
                              {doc.original_name}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          <Badge variant="outline">{doc.document_type || "PDF"}</Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary" className="text-xs">
                            {doc.chunk_count}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center text-sm font-mono text-muted-foreground">
                          v{doc.version || 1}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={doc.status === "ACTIVE" ? "default" : doc.status === "ARCHIVED" ? "secondary" : "destructive"} 
                            className="text-[10px]"
                          >
                            {doc.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {formatDate(doc.last_indexed || doc.created_at)}
                        </TableCell>
                        {canManage && (
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="h-8 w-8 p-0">
                                  <span className="sr-only">Open menu</span>
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                {doc.status === "ACTIVE" && (
                                  <>
                                    <DropdownMenuItem onClick={() => triggerReplace(doc.id)}>
                                      <FileUp className="mr-2 h-4 w-4" /> Replace (New Version)
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => {
                                      if (confirm("Are you sure you want to re-index this document?")) {
                                        reindexMutation.mutate(doc.id);
                                      }
                                    }}>
                                      <RefreshCw className="mr-2 h-4 w-4" /> Re-index
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={() => {
                                      if (confirm("Are you sure you want to archive this document? It will not be searchable.")) {
                                        archiveMutation.mutate(doc.id);
                                      }
                                    }}>
                                      <Archive className="mr-2 h-4 w-4" /> Archive
                                    </DropdownMenuItem>
                                  </>
                                )}
                                <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => {
                                  if (confirm("Are you sure you want to permanently delete this document?")) {
                                    deleteMutation.mutate(doc.id);
                                  }
                                }}>
                                  <Trash2 className="mr-2 h-4 w-4" /> Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </AppShell>
  );
}
