"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  MillingBatch,
  MillingBatchDetail,
  Page,
  PaddyLotWithStock,
  RiceProduction,
} from "@/lib/types";

export function usePaddyLots() {
  return useQuery({
    queryKey: ["paddy-lots"],
    queryFn: () =>
      apiFetch<Page<PaddyLotWithStock>>("/paddy-lots?page_size=100"),
  });
}

export function useBatches(page = 1) {
  return useQuery({
    queryKey: ["batches", page],
    queryFn: () =>
      apiFetch<Page<MillingBatch>>(`/milling-batches?page=${page}`),
  });
}

export function useBatch(id: string) {
  return useQuery({
    queryKey: ["batch", id],
    queryFn: () => apiFetch<MillingBatchDetail>(`/milling-batches/${id}`),
    enabled: Boolean(id),
  });
}

export function useCreateBatch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      inputs: { paddy_lot_id: string; quantity_kg: string }[];
      notes?: string;
    }) =>
      apiFetch<MillingBatchDetail>("/milling-batches", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["batches"] }),
  });
}

function invalidateBatch(qc: ReturnType<typeof useQueryClient>, id: string) {
  qc.invalidateQueries({ queryKey: ["batches"] });
  qc.invalidateQueries({ queryKey: ["batch", id] });
  qc.invalidateQueries({ queryKey: ["paddy-lots"] });
  qc.invalidateQueries({ queryKey: ["rice-quality"] });
}

export function useStartBatch(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<MillingBatchDetail>(`/milling-batches/${id}/start`, {
        method: "POST",
      }),
    onSuccess: () => invalidateBatch(qc, id),
  });
}

export function useRecordProduction(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      outputs: {
        category: string;
        quantity_kg: string;
        bag_weight_kg: string;
      }[];
      notes?: string;
    }) =>
      apiFetch<RiceProduction>(`/milling-batches/${id}/productions`, {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => invalidateBatch(qc, id),
  });
}

export function useCompleteBatch(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<MillingBatchDetail>(`/milling-batches/${id}/complete`, {
        method: "POST",
      }),
    onSuccess: () => invalidateBatch(qc, id),
  });
}
