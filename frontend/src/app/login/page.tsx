"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plane } from "lucide-react";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import apiClient from "@/lib/api-client";
import type { LoginResponse } from "@/types/api";

const DEFAULT_CREDENTIALS = [
  { role: "admin", password: "Admin123!" },
  { role: "analyst", password: "Analyst123!" },
  { role: "viewer", password: "Viewer123!" },
];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const { data } = await apiClient.post<LoginResponse>("/login", {
        username,
        password,
      });
      login(data.access_token, data.user);
      router.push("/dashboard");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(
        axiosErr.response?.data?.detail ?? "Invalid username or password."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const fillCredentials = (role: string, pwd: string) => {
    setUsername(role);
    setPassword(pwd);
    setError("");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <Plane className="h-7 w-7 text-primary" />
          </div>
          <div>
            <CardTitle className="text-xl">Airport AI Platform</CardTitle>
            <CardDescription>
              Sign in to access operations monitoring
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                autoComplete="username"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>
            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}
            <Button
              id="login-submit-btn"
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          {/* Quick-fill demo credentials */}
          <div className="mt-6 border-t pt-4">
            <p className="mb-3 text-center text-xs text-muted-foreground">
              Demo accounts — click to fill
            </p>
            <div className="flex gap-2">
              {DEFAULT_CREDENTIALS.map(({ role, password: pwd }) => (
                <button
                  key={role}
                  type="button"
                  id={`demo-${role}-btn`}
                  onClick={() => fillCredentials(role, pwd)}
                  className="flex-1 rounded-md border border-dashed px-2 py-1.5 text-center text-xs capitalize text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                >
                  {role}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
