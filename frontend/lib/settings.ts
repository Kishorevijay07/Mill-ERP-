"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { ChargeRate, ChargeUnit, MillSettings } from "@/lib/types";

export function useMillSettings() {
  return useQuery({
    queryKey: ["mill-settings"],
    queryFn: () => apiFetch<MillSettings>("/mill-settings"),
  });
}

export function useUpdateMillSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (
      input: Partial<MillSettings> & { name: string; currency: string },
    ) =>
      apiFetch<MillSettings>("/mill-settings", {
        method: "PUT",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mill-settings"] }),
  });
}

export function useChargeRates() {
  return useQuery({
    queryKey: ["charge-rates"],
    queryFn: () => apiFetch<ChargeRate[]>("/charge-rates"),
  });
}

export function useCreateChargeRate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      code: string;
      label: string;
      rate: string;
      unit: ChargeUnit;
      is_deduction: boolean;
      is_active: boolean;
    }) =>
      apiFetch<ChargeRate>("/charge-rates", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["charge-rates"] }),
  });
}

export function useDeleteChargeRate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/charge-rates/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["charge-rates"] }),
  });
}
