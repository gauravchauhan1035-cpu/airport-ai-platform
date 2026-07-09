"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader
        title="Settings"
        description="Application configuration and preferences"
      />

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
            <CardDescription>Platform information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Airport AI Platform v0.1.0</p>
            <p className="text-muted-foreground">
              Local-first AI operations monitoring with SQL and RAG routing.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
