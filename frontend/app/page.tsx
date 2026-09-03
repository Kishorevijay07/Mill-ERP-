"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";

interface HealthResponse {
  status: string;
  app: string;
  environment: string;
  version: string;
}

function useBackendHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => {
      // /health is a root-level probe, outside the /api/v1 prefix.
      const base =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
      const origin = new URL(base).origin;
      return apiFetch<HealthResponse>(`${origin}/health`);
    },
  });
}

export default function HomePage() {
  const { data, isLoading, isError } = useBackendHealth();

  const state = isLoading
    ? { label: "Checking backend…", tone: "muted" as const }
    : isError
      ? { label: "Backend unreachable", tone: "error" as const }
      : { label: `Backend healthy · v${data?.version}`, tone: "ok" as const };

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 p-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Rice Mill ERP</h1>
        <p className="text-muted-foreground">
          Phase 0 foundation. Business modules are added from Stage 1 onward.
        </p>
      </header>

      <div
        className={cn(
          "rounded-lg border p-4 text-sm",
          state.tone === "ok" && "border-primary/40 bg-primary/5",
          state.tone === "error" && "border-red-300 bg-red-50 text-red-700",
          state.tone === "muted" && "bg-muted text-muted-foreground",
        )}
      >
        <span className="font-medium">Status:</span> {state.label}
      </div>

      <ol className="list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
        <li>Authentication &amp; roles</li>
        <li>Government receiving (allocations → loads → paddy lots)</li>
        <li>Milling &amp; rice production</li>
        <li>Delivery, claims &amp; payments</li>
      </ol>
    </main>
  );
}
