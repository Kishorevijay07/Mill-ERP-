"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  DeliveryReceipt,
  Dispatch,
  DispatchDetail,
  Page,
} from "@/lib/types";

export function useDispatches(page = 1) {
  return useQuery({
    queryKey: ["dispatches", page],
    queryFn: () => apiFetch<Page<Dispatch>>(`/dispatches?page=${page}`),
  });
}

export function useDispatch(id: string) {
  return useQuery({
    queryKey: ["dispatch", id],
    queryFn: () => apiFetch<DispatchDetail>(`/dispatches/${id}`),
    enabled: Boolean(id),
  });
}

export function useReceipts(page = 1) {
  return useQuery({
    queryKey: ["receipts", page],
    queryFn: () =>
      apiFetch<Page<DeliveryReceipt>>(`/delivery-receipts?page=${page}`),
  });
}

export function useCreateDispatch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      destination_name: string;
      lorry_number: string;
      items: { rice_lot_id: string; quantity_kg: string }[];
      delivery_order_id?: string;
    }) =>
      apiFetch<DispatchDetail>("/dispatches", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dispatches"] }),
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>, id: string) {
  qc.invalidateQueries({ queryKey: ["dispatches"] });
  qc.invalidateQueries({ queryKey: ["dispatch", id] });
  qc.invalidateQueries({ queryKey: ["rice-lots"] });
  qc.invalidateQueries({ queryKey: ["receipts"] });
}

export function usePrepareDispatch(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<DispatchDetail>(`/dispatches/${id}/prepare`, { method: "POST" }),
    onSuccess: () => invalidate(qc, id),
  });
}

export function useDispatchDispatch(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<DispatchDetail>(`/dispatches/${id}/dispatch`, {
        method: "POST",
      }),
    onSuccess: () => invalidate(qc, id),
  });
}

export function useCreateReceipt(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      received_quantity_kg: string;
      received_bags?: number;
      receipt_number?: string;
      receipt_date?: string;
    }) =>
      apiFetch<DeliveryReceipt>(`/dispatches/${id}/delivery-receipt`, {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => invalidate(qc, id),
  });
}
