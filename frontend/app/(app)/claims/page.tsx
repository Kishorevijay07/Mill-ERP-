"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { useClaims, useCreateClaim } from "@/lib/billing";
import { useReceipts } from "@/lib/delivery";
import { formatDate, formatKg, formatMoney } from "@/lib/format";
import { useAgencies } from "@/lib/government";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Select } from "@/components/ui/input";
import {
  EmptyState,
  ErrorNote,
  Spinner,
  StatusPill,
} from "@/components/ui/misc";

function NewClaimForm({ onClose }: { onClose: () => void }) {
  const { data: agencies } = useAgencies();
  const { data: receipts } = useReceipts();
  const create = useCreateClaim();
  const [agencyId, setAgencyId] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const receiptItems = receipts?.items ?? [];

  function toggle(id: string) {
    setSelected((s) =>
      s.includes(id) ? s.filter((x) => x !== id) : [...s, id],
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { agency_id: agencyId, delivery_receipt_ids: selected },
      { onSuccess: onClose },
    );
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>New claim</CardTitle>
      </CardHeader>
      <CardContent>
        {receiptItems.length === 0 ? (
          <EmptyState>No delivery receipts to claim yet.</EmptyState>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <Field label="Government agency">
              <Select
                value={agencyId}
                onChange={(e) => setAgencyId(e.target.value)}
                required
              >
                <option value="" disabled>
                  Select agency
                </option>
                {(agencies?.items ?? []).map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.code} — {a.name}
                  </option>
                ))}
              </Select>
            </Field>
            <div>
              <p className="mb-1 text-sm font-medium">
                Delivery receipts to claim
              </p>
              <div className="space-y-1 rounded-md border border-border p-3">
                {receiptItems.map((r) => (
                  <label key={r.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selected.includes(r.id)}
                      onChange={() => toggle(r.id)}
                    />
                    {r.reference} · received {formatKg(r.received_quantity_kg)}
                  </label>
                ))}
              </div>
            </div>
            <ErrorNote
              message={
                create.error instanceof ApiError
                  ? create.error.message
                  : undefined
              }
            />
            <div className="flex gap-2">
              <Button
                type="submit"
                disabled={
                  create.isPending || !agencyId || selected.length === 0
                }
              >
                {create.isPending ? "Creating…" : "Create claim"}
              </Button>
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

export default function ClaimsPage() {
  const { data, isLoading, isError } = useClaims();
  const [creating, setCreating] = useState(false);
  const can = useHasPermission();

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Claims &amp; Payments</h1>
        {can("billing.create") && !creating ? (
          <Button onClick={() => setCreating(true)}>New claim</Button>
        ) : null}
      </div>
      {creating ? <NewClaimForm onClose={() => setCreating(false)} /> : null}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load claims." />
      ) : !data || data.items.length === 0 ? (
        <EmptyState>No claims yet.</EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Reference</th>
                  <th className="p-3 font-medium">Net</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Created</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr
                    key={c.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{c.reference}</td>
                    <td className="p-3">
                      {formatMoney(c.net_amount, c.currency)}
                    </td>
                    <td className="p-3">
                      <StatusPill status={c.status} />
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {formatDate(c.created_at)}
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        href={`/claims/${c.id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
