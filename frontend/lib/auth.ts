"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Me } from "@/lib/types";

export const meKey = ["me"] as const;

/** Current authenticated user; `isError` means not logged in (401). */
export function useMe() {
  return useQuery({
    queryKey: meKey,
    queryFn: () => apiFetch<Me>("/auth/me"),
    retry: false,
    staleTime: 60_000,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { identifier: string; password: string }) =>
      apiFetch<Me>("/auth/login", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: (data) => {
      qc.setQueryData(meKey, data);
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<{ message: string }>("/auth/logout", { method: "POST" }),
    onSuccess: () => {
      qc.clear();
    },
  });
}

/** Convenience permission check against the current user. */
export function useHasPermission() {
  const { data } = useMe();
  const perms = new Set(data?.permissions ?? []);
  return (code: string) => perms.has(code);
}
