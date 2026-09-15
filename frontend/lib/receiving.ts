"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  AcceptResponse,
  GovernmentLoad,
  Page,
  PaddyLotWithStock,
  PaddyQuality,
  Weighment,
} from "@/lib/types";

export function usePaddyLots() {
  return useQuery({
    queryKey: ["paddy-lots"],
    queryFn: () =>
      apiFetch<Page<PaddyLotWithStock>>("/paddy-lots?page_size=100"),
  });
}

function invalidateLoad(qc: ReturnType<typeof useQueryClient>, loadId: string) {
  qc.invalidateQueries({ queryKey: ["load", loadId] });
  qc.invalidateQueries({ queryKey: ["loads"] });
  qc.invalidateQueries({ queryKey: ["weighments", loadId] });
  qc.invalidateQueries({ queryKey: ["paddy-quality", loadId] });
  qc.invalidateQueries({ queryKey: ["paddy-lots"] });
}

export function useWeighments(loadId: string) {
  return useQuery({
    queryKey: ["weighments", loadId],
    queryFn: () =>
      apiFetch<Weighment[]>(`/government-loads/${loadId}/weighments`),
    enabled: Boolean(loadId),
  });
}

export function usePaddyQuality(loadId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["paddy-quality", loadId],
    queryFn: () =>
      apiFetch<PaddyQuality>(`/government-loads/${loadId}/paddy-quality`),
    enabled: Boolean(loadId) && enabled,
    retry: false,
  });
}

export function useRecordWeighment(loadId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      gross_kg: string;
      tare_kg: string;
      weighbridge_ref?: string;
    }) =>
      apiFetch<Weighment>(`/government-loads/${loadId}/weighments`, {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => invalidateLoad(qc, loadId),
  });
}

export function useRecordQuality(loadId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      moisture_pct: string;
      foreign_matter_pct: string;
      damaged_pct: string;
      notes?: string;
    }) =>
      apiFetch<PaddyQuality>(`/government-loads/${loadId}/paddy-quality`, {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => invalidateLoad(qc, loadId),
  });
}

export function useAcceptLoad(loadId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<AcceptResponse>(`/government-loads/${loadId}/accept`, {
        method: "POST",
      }),
    onSuccess: () => invalidateLoad(qc, loadId),
  });
}

export function useRejectLoad(loadId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reason?: string) =>
      apiFetch<GovernmentLoad>(`/government-loads/${loadId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: reason ?? null }),
      }),
    onSuccess: () => invalidateLoad(qc, loadId),
  });
}
