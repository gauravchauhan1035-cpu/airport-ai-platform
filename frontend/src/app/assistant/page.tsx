"use client";

import { useRef, useState } from "react";
import { Bot, Code2, Database, Send, User } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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
import apiClient from "@/lib/api-client";
import type { AskResponse } from "@/types/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  question?: string;
  response?: AskResponse;
  error?: string;
  timestamp: Date;
}

const SAMPLE_QUESTIONS = [
  "What is the average temperature in Terminal 1?",
  "Show the latest security wait time readings",
  "Which zone has the highest passenger count?",
  "What is the average wind speed on the runway?",
];

const ROUTE_COLORS: Record<string, string> = {
  SQL: "bg-blue-100 text-blue-700",
  RAG: "bg-green-100 text-green-700",
  BOTH: "bg-purple-100 text-purple-700",
};

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const inputRef = useRef<HTMLInputElement>(null);

  const sendQuestion = async (q: string) => {
    if (!q.trim() || isLoading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      question: q,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setIsLoading(true);

    try {
      const { data } = await apiClient.post<AskResponse>("/query", {
        question: q,
        session_id: sessionId,
      });

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        response: data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const errMsg =
        axiosErr.response?.data?.detail ??
        "An error occurred. Please try again.";
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        error: errMsg,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuestion(question);
  };

  return (
    <AppShell>
      <PageHeader
        title="AI Assistant"
        description="Ask natural language questions about airport operations — powered by Ollama"
      />

      <div className="flex flex-col gap-6 lg:flex-row">
        {/* ── Chat Panel ── */}
        <div className="flex flex-1 flex-col gap-4">
          {/* Sample questions */}
          {messages.length === 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Try asking…</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {SAMPLE_QUESTIONS.map((sq) => (
                  <button
                    key={sq}
                    type="button"
                    onClick={() => sendQuestion(sq)}
                    className="rounded-full border border-dashed px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                  >
                    {sq}
                  </button>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Message list */}
          <div className="flex flex-col gap-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                {/* Avatar */}
                <div
                  className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  {msg.role === "user" ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>

                {/* Bubble */}
                <div className={`max-w-[85%] ${msg.role === "user" ? "items-end" : ""} flex flex-col gap-2`}>
                  {msg.role === "user" && msg.question && (
                    <div className="rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                      {msg.question}
                    </div>
                  )}

                  {msg.error && (
                    <div className="rounded-2xl rounded-tl-sm bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
                      {msg.error}
                    </div>
                  )}

                  {msg.response && (
                    <div className="flex flex-col gap-3">
                      {/* Answer card */}
                      <Card>
                        <CardHeader className="pb-2 pt-4">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-sm">Answer</CardTitle>
                            <div className="flex items-center gap-2">
                              {msg.response.route.split(",").map((r) => (
                                <span
                                  key={r}
                                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                    r === "SQL" ? "bg-blue-100 text-blue-700" :
                                    r === "RAG" ? "bg-green-100 text-green-700" :
                                    r === "CHAT" ? "bg-purple-100 text-purple-700" :
                                    "bg-gray-100 text-gray-700"
                                  }`}
                                >
                                  {r}
                                </span>
                              ))}
                              <span className="text-xs text-muted-foreground">
                                {msg.response.execution_time_ms}ms
                              </span>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="whitespace-pre-wrap text-sm">
                            {msg.response.answer}
                          </p>
                        </CardContent>
                      </Card>

                      {/* Generated SQL */}
                      {msg.response.sql && (
                        <Card>
                          <CardHeader className="pb-2 pt-4">
                            <CardTitle className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Code2 className="h-3.5 w-3.5" />
                              Generated SQL
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <pre className="overflow-x-auto rounded-md bg-muted px-4 py-3 text-xs">
                              {msg.response.sql}
                            </pre>
                          </CardContent>
                        </Card>
                      )}

                      {/* SQL Results table */}
                      {msg.response.sql_rows && msg.response.sql_rows.length > 0 && (
                        <Card>
                          <CardHeader className="pb-2 pt-4">
                            <CardTitle className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Database className="h-3.5 w-3.5" />
                              Results ({msg.response.row_count ?? msg.response.sql_rows.length} rows)
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="p-0">
                            <div className="overflow-x-auto">
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    {Object.keys(msg.response.sql_rows[0]).map((col) => (
                                      <TableHead key={col} className="text-xs">
                                        {col}
                                      </TableHead>
                                    ))}
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {msg.response.sql_rows.slice(0, 20).map((row, i) => (
                                    <TableRow key={i}>
                                      {Object.values(row).map((val, j) => (
                                        <TableCell key={j} className="text-xs">
                                          {String(val ?? "—")}
                                        </TableCell>
                                      ))}
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* RAG chunks */}
                      {msg.response.retrieved_chunks && msg.response.retrieved_chunks.length > 0 && (
                        <Card>
                          <CardHeader className="pb-2 pt-4">
                            <CardTitle className="text-xs text-muted-foreground">
                              Retrieved Documents ({msg.response.retrieved_chunks.length})
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            {msg.response.retrieved_chunks.map((chunk, i) => (
                              <div key={i} className="rounded-md border p-3">
                                <p className="text-xs font-medium">
                                  {chunk.document_name} — Page {chunk.page_number}
                                  <Badge variant="secondary" className="ml-2 text-xs">
                                    {(chunk.score * 100).toFixed(0)}% match
                                  </Badge>
                                </p>
                                <p className="mt-2 text-xs text-muted-foreground line-clamp-3">
                                  {chunk.content}
                                </p>
                              </div>
                            ))}
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  )}

                  <span className="text-[10px] text-muted-foreground">
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-muted">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-muted px-4 py-2.5">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <Card className="sticky bottom-0 mt-auto">
            <CardContent className="pt-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  ref={inputRef}
                  id="assistant-question-input"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask about airport operations..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button
                  id="assistant-ask-btn"
                  type="submit"
                  disabled={isLoading || !question.trim()}
                  size="icon"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* ── Info Panel ── */}
        <div className="w-full lg:w-72">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">How it works</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground">
              <div className="flex items-start gap-2">
                <span className="mt-0.5 rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700">SQL</span>
                <p>Questions about metrics, numbers, and trends are answered by querying the SQLite database via the AI model.</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="mt-0.5 rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-medium text-green-700">RAG</span>
                <p>Procedural and policy questions are answered by searching uploaded PDF documents semantically.</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="mt-0.5 rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-medium text-purple-700">CHAT</span>
                <p>General conversation, context memory, and response synthesis are handled by the Chat agent.</p>
              </div>
            </CardContent>
          </Card>

          {messages.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              className="mt-4 w-full"
              onClick={() => setMessages([])}
            >
              Clear conversation
            </Button>
          )}
        </div>
      </div>
    </AppShell>
  );
}
