"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  Agency,
  Allocation,
  DeliveryOrder,
  GovernmentLoad,
  Page,
} from "@/lib/types";

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") search.set(k, String(v));
  }
  const s = search.toString();
  return s ? `?${s}` : "";
}

// ---- Agencies ----
export function useAgencies() {
  return useQuery({
    queryKey: ["agencies"],
    queryFn: () =>
      apiFetch<Page<Agency>>(`/government-agencies${qs({ page_size: 100 })}`),
  });
}

export function useCreateAgency() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      code: string;
      name: string;
      contact_name?: string;
      contact_phone?: string;
    }) =>
      apiFetch<Agency>("/government-agencies", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agencies"] }),
  });
}

// ---- Allocations ----
export function useAllocations() {
  return useQuery({
    queryKey: ["allocations"],
    queryFn: () =>
      apiFetch<Page<Allocation>>(`/allocations${qs({ page_size: 100 })}`),
  });
}

export function useCreateAllocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      agency_id: string;
      quantity_kg: string;
      allocated_on: string;
      season?: string;
    }) =>
      apiFetch<Allocation>("/allocations", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["allocations"] }),
  });
}

// ---- Delivery orders ----
export function useDeliveryOrders() {
  return useQuery({
    queryKey: ["delivery-orders"],
    queryFn: () =>
      apiFetch<Page<DeliveryOrder>>(
        `/delivery-orders${qs({ page_size: 100 })}`,
      ),
  });
}

export function useCreateDeliveryOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      allocation_id: string;
      do_number: string;
      quantity_kg: string;
      issued_on: string;
    }) =>
      apiFetch<DeliveryOrder>("/delivery-orders", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["delivery-orders"] }),
  });
}

// ---- Government loads ----
export function useLoads(page = 1) {
  return useQuery({
    queryKey: ["loads", page],
    queryFn: () =>
      apiFetch<Page<GovernmentLoad>>(`/government-loads${qs({ page })}`),
  });
}

export function useLoad(id: string) {
  return useQuery({
    queryKey: ["load", id],
    queryFn: () => apiFetch<GovernmentLoad>(`/government-loads/${id}`),
    enabled: Boolean(id),
  });
}

export function useCreateLoad() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      delivery_order_id: string;
      lorry_number: string;
      driver_name?: string;
      declared_quantity_kg?: string;
    }) =>
      apiFetch<GovernmentLoad>("/government-loads", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["loads"] }),
  });
}

export function useArriveLoad() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (loadId: string) =>
      apiFetch<GovernmentLoad>(`/government-loads/${loadId}/arrive`, {
        method: "POST",
      }),
    onSuccess: (load) => {
      qc.invalidateQueries({ queryKey: ["loads"] });
      qc.invalidateQueries({ queryKey: ["load", load.id] });
    },
  });
}
