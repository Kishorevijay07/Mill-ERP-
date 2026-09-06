"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Page, RiceLotWithStock, RiceQuality } from "@/lib/types";

export function useRiceQuality(status?: string) {
  const q = status ? `?status=${status}&page_size=100` : "?page_size=100";
  return useQuery({
    queryKey: ["rice-quality", status ?? "all"],
    queryFn: () => apiFetch<Page<RiceQuality>>(`/rice-quality${q}`),
  });
}

export function useRiceLots() {
  return useQuery({
    queryKey: ["rice-lots"],
    queryFn: () => apiFetch<Page<RiceLotWithStock>>("/rice-lots?page_size=100"),
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["rice-quality"] });
  qc.invalidateQueries({ queryKey: ["rice-lots"] });
}

export function usePassQuality() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/rice-quality/${id}/pass`, { method: "POST" }),
    onSuccess: () => invalidate(qc),
  });
}

export function useFailQuality() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { id: string; notes?: string }) =>
      apiFetch(`/rice-quality/${input.id}/fail`, {
        method: "POST",
        body: JSON.stringify({ notes: input.notes ?? null }),
      }),
    onSuccess: () => invalidate(qc),
  });
}
