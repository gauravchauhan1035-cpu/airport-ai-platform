"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader, PlaceholderPanel } from "@/components/layout/page-header";
import { useAuth } from "@/components/providers/auth-provider";

export default function LogsPage() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (user?.role !== "admin") {
    return null;
  }

  return (
    <AppShell>
      <PageHeader
        title="Audit Logs"
        description="Admin-only view of questions, routes, SQL, and errors"
      />
      <PlaceholderPanel
        title="Audit logs coming in Phase 3–8"
        description="Will display timestamp, user, question, route, generated SQL, execution time, and errors."
      />
    </AppShell>
  );
}
