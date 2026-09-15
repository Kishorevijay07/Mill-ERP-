"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Claim, ClaimDetail, Page } from "@/lib/types";

export function useClaims(page = 1) {
  return useQuery({
    queryKey: ["claims", page],
    queryFn: () => apiFetch<Page<Claim>>(`/government-claims?page=${page}`),
  });
}

export function useClaim(id: string) {
  return useQuery({
    queryKey: ["claim", id],
    queryFn: () => apiFetch<ClaimDetail>(`/government-claims/${id}`),
    enabled: Boolean(id),
  });
}

export function useCreateClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      agency_id: string;
      delivery_receipt_ids: string[];
    }) =>
      apiFetch<ClaimDetail>("/government-claims", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claims"] }),
  });
}

function invalidate(qc: ReturnType<typeof useQueryClient>, id: string) {
  qc.invalidateQueries({ queryKey: ["claims"] });
  qc.invalidateQueries({ queryKey: ["claim", id] });
}

export function useReplaceLines(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (
      lines: {
        description: string;
        quantity: string;
        rate: string;
        is_deduction: boolean;
      }[],
    ) =>
      apiFetch<ClaimDetail>(`/government-claims/${id}/lines`, {
        method: "PUT",
        body: JSON.stringify({ lines }),
      }),
    onSuccess: () => invalidate(qc, id),
  });
}

export function useSubmitClaim(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<ClaimDetail>(`/government-claims/${id}/submit`, {
        method: "POST",
      }),
    onSuccess: () => invalidate(qc, id),
  });
}

export function useApproveClaim(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<ClaimDetail>(`/government-claims/${id}/approve`, {
        method: "POST",
      }),
    onSuccess: () => invalidate(qc, id),
  });
}

export function useGenerateInvoice(id: string) {
  return useMutation({
    mutationFn: () =>
      apiFetch<{ document_id: string; filename: string }>(
        `/government-claims/${id}/invoice`,
        { method: "POST" },
      ),
  });
}

export function useRecordPayment(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      amount: string;
      paid_on?: string;
      method?: string;
      reference_no?: string;
    }) =>
      apiFetch(`/payments`, {
        method: "POST",
        body: JSON.stringify({ claim_id: id, ...input }),
      }),
    onSuccess: () => invalidate(qc, id),
  });
}

/** Fetch the invoice PDF (with session cookie) and trigger a browser download. */
export async function downloadInvoice(
  documentId: string,
  filename: string,
): Promise<void> {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const res = await fetch(`${base}/documents/${documentId}/download`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to download invoice");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
