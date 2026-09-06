"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { useCreateDispatch, useDispatches } from "@/lib/delivery";
import { formatDate, formatKg } from "@/lib/format";
import { useRiceLots } from "@/lib/rice";
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

type Row = { rice_lot_id: string; quantity_kg: string };

function NewDispatchForm({ onClose }: { onClose: () => void }) {
  const { data: lots } = useRiceLots();
  const create = useCreateDispatch();
  const [destination, setDestination] = useState("");
  const [lorry, setLorry] = useState("");
  const [rows, setRows] = useState<Row[]>([
    { rice_lot_id: "", quantity_kg: "" },
  ]);
  const available = (lots?.items ?? []).filter(
    (l) => Number(l.available_kg) > 0,
  );
  const availableById = new Map(
    available.map((l) => [l.id, Number(l.available_kg)]),
  );

  // Requested total per lot across all rows — a lot can be split over rows, so a
  // single row can look fine while the lot is collectively overspent.
  const requestedByLot = new Map<string, number>();
  for (const r of rows) {
    if (!r.rice_lot_id || !r.quantity_kg) continue;
    requestedByLot.set(
      r.rice_lot_id,
      (requestedByLot.get(r.rice_lot_id) ?? 0) + Number(r.quantity_kg),
    );
  }

  function rowError(row: Row): string | undefined {
    if (!row.rice_lot_id || !row.quantity_kg) return undefined;
    const avail = availableById.get(row.rice_lot_id);
    if (avail === undefined) return undefined;
    const requested = requestedByLot.get(row.rice_lot_id) ?? 0;
    if (requested > avail) {
      return `Exceeds available (${formatKg(avail)}) for this lot`;
    }
    return undefined;
  }

  const hasErrors = rows.some((r) => rowError(r) !== undefined);

  function update(i: number, patch: Partial<Row>) {
    setRows((r) =>
      r.map((row, idx) => (idx === i ? { ...row, ...patch } : row)),
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (hasErrors) return;
    create.mutate(
      {
        destination_name: destination,
        lorry_number: lorry,
        items: rows.filter((r) => r.rice_lot_id && r.quantity_kg),
      },
      { onSuccess: onClose },
    );
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>New dispatch</CardTitle>
      </CardHeader>
      <CardContent>
        {available.length === 0 ? (
          <EmptyState>
            No rice stock available. Pass a rice QC first.
          </EmptyState>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Destination">
                <Input
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  required
                />
              </Field>
              <Field label="Lorry number">
                <Input
                  value={lorry}
                  onChange={(e) => setLorry(e.target.value)}
                  required
                />
              </Field>
            </div>
            {rows.map((row, i) => {
              const rowAvail = row.rice_lot_id
                ? availableById.get(row.rice_lot_id)
                : undefined;
              return (
                <div key={i} className="grid gap-3 sm:grid-cols-2">
                  <Field label="Rice lot">
                    <Select
                      value={row.rice_lot_id}
                      onChange={(e) =>
                        update(i, { rice_lot_id: e.target.value })
                      }
                      required
                    >
                      <option value="" disabled>
                        Select rice lot
                      </option>
                      {available.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.reference} · {l.category.replace("_", " ")} ·{" "}
                          {formatKg(l.available_kg)}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Quantity (kg)" error={rowError(row)}>
                    <Input
                      type="number"
                      step="0.001"
                      min="0.001"
                      max={rowAvail}
                      value={row.quantity_kg}
                      onChange={(e) =>
                        update(i, { quantity_kg: e.target.value })
                      }
                      required
                    />
                    {rowAvail !== undefined ? (
                      <p className="text-xs text-muted-foreground">
                        Available: {formatKg(rowAvail)}
                      </p>
                    ) : null}
                  </Field>
                </div>
              );
            })}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setRows((r) => [...r, { rice_lot_id: "", quantity_kg: "" }])
              }
            >
              + Add lot
            </Button>
            <ErrorNote
              message={
                create.error instanceof ApiError
                  ? create.error.message
                  : undefined
              }
            />
            <div className="flex gap-2">
              <Button type="submit" disabled={create.isPending || hasErrors}>
                {create.isPending ? "Creating…" : "Create dispatch"}
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

export default function DispatchPage() {
  const { data, isLoading, isError } = useDispatches();
  const [creating, setCreating] = useState(false);
  const can = useHasPermission();

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dispatch</h1>
        {can("dispatch.create") && !creating ? (
          <Button onClick={() => setCreating(true)}>New dispatch</Button>
        ) : null}
      </div>
      {creating ? <NewDispatchForm onClose={() => setCreating(false)} /> : null}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load dispatches." />
      ) : !data || data.items.length === 0 ? (
        <EmptyState>No dispatches yet.</EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Reference</th>
                  <th className="p-3 font-medium">Destination</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Created</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {data.items.map((d) => (
                  <tr
                    key={d.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{d.reference}</td>
                    <td className="p-3">{d.destination_name}</td>
                    <td className="p-3">
                      <StatusPill status={d.status} />
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {formatDate(d.created_at)}
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        href={`/dispatch/${d.id}`}
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
