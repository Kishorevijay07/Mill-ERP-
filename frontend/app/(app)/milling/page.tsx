"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { formatKg } from "@/lib/format";
import { useBatches, useCreateBatch, usePaddyLots } from "@/lib/milling";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import {
  EmptyState,
  ErrorNote,
  Spinner,
  StatusPill,
} from "@/components/ui/misc";

type Row = { paddy_lot_id: string; quantity_kg: string };

function NewBatchForm({ onClose }: { onClose: () => void }) {
  const { data: lots } = usePaddyLots();
  const create = useCreateBatch();
  const [rows, setRows] = useState<Row[]>([
    { paddy_lot_id: "", quantity_kg: "" },
  ]);
  const available = (lots?.items ?? []).filter(
    (l) => Number(l.available_kg) > 0,
  );

  function update(i: number, patch: Partial<Row>) {
    setRows((r) =>
      r.map((row, idx) => (idx === i ? { ...row, ...patch } : row)),
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { inputs: rows.filter((r) => r.paddy_lot_id && r.quantity_kg) },
      { onSuccess: onClose },
    );
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>New milling batch</CardTitle>
      </CardHeader>
      <CardContent>
        {available.length === 0 ? (
          <EmptyState>
            No paddy stock available. Accept a load first.
          </EmptyState>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            {rows.map((row, i) => (
              <div key={i} className="grid gap-3 sm:grid-cols-2">
                <Field label="Paddy lot">
                  <Select
                    value={row.paddy_lot_id}
                    onChange={(e) =>
                      update(i, { paddy_lot_id: e.target.value })
                    }
                    required
                  >
                    <option value="" disabled>
                      Select paddy lot
                    </option>
                    {available.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.reference} · {formatKg(l.available_kg)} available
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Quantity to consume (kg)">
                  <Input
                    type="number"
                    step="0.001"
                    min="0.001"
                    value={row.quantity_kg}
                    onChange={(e) => update(i, { quantity_kg: e.target.value })}
                    required
                  />
                </Field>
              </div>
            ))}
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  setRows((r) => [...r, { paddy_lot_id: "", quantity_kg: "" }])
                }
              >
                + Add lot
              </Button>
            </div>
            <ErrorNote
              message={
                create.error instanceof ApiError
                  ? create.error.message
                  : undefined
              }
            />
            <div className="flex gap-2">
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Creating…" : "Create batch"}
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

export default function MillingPage() {
  const { data, isLoading, isError } = useBatches();
  const [creating, setCreating] = useState(false);
  const can = useHasPermission();

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Milling Batches</h1>
        {can("milling.batch.create") && !creating ? (
          <Button onClick={() => setCreating(true)}>New batch</Button>
        ) : null}
      </div>
      {creating ? <NewBatchForm onClose={() => setCreating(false)} /> : null}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load batches." />
      ) : !data || data.items.length === 0 ? (
        <EmptyState>No milling batches yet.</EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Reference</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Created</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {data.items.map((b) => (
                  <tr
                    key={b.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{b.reference}</td>
                    <td className="p-3">
                      <StatusPill status={b.status} />
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {new Date(b.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        href={`/milling/${b.id}`}
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
