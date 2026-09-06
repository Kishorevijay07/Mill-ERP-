"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { formatKg } from "@/lib/format";
import {
  useBatch,
  useCompleteBatch,
  useRecordProduction,
  useStartBatch,
} from "@/lib/milling";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import { ErrorNote, Spinner, StatusPill } from "@/components/ui/misc";

function msg(e: unknown): string | undefined {
  return e instanceof ApiError ? e.message : undefined;
}

type Out = { category: string; quantity_kg: string; bag_weight_kg: string };

function ProductionForm({ batchId }: { batchId: string }) {
  const record = useRecordProduction(batchId);
  const [outs, setOuts] = useState<Out[]>([
    { category: "CATEGORY_1", quantity_kg: "", bag_weight_kg: "50" },
  ]);

  function update(i: number, patch: Partial<Out>) {
    setOuts((o) =>
      o.map((row, idx) => (idx === i ? { ...row, ...patch } : row)),
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    record.mutate(
      { outputs: outs.filter((o) => o.quantity_kg && o.bag_weight_kg) },
      {
        onSuccess: () =>
          setOuts([
            { category: "CATEGORY_1", quantity_kg: "", bag_weight_kg: "50" },
          ]),
      },
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      {outs.map((o, i) => {
        const bags =
          o.quantity_kg && Number(o.bag_weight_kg) > 0
            ? Math.floor(Number(o.quantity_kg) / Number(o.bag_weight_kg))
            : null;
        return (
          <div key={i} className="grid gap-3 sm:grid-cols-4">
            <Field label="Category">
              <Select
                value={o.category}
                onChange={(e) => update(i, { category: e.target.value })}
              >
                <option value="CATEGORY_1">Category 1</option>
                <option value="CATEGORY_2">Category 2</option>
              </Select>
            </Field>
            <Field label="Quantity (kg)">
              <Input
                type="number"
                step="0.001"
                min="0.001"
                value={o.quantity_kg}
                onChange={(e) => update(i, { quantity_kg: e.target.value })}
                required
              />
            </Field>
            <Field label="Bag weight (kg)">
              <Input
                type="number"
                step="0.001"
                min="0.001"
                value={o.bag_weight_kg}
                onChange={(e) => update(i, { bag_weight_kg: e.target.value })}
                required
              />
            </Field>
            <div className="flex items-end text-sm text-muted-foreground">
              Bags:{" "}
              <span className="ml-1 font-medium text-foreground">
                {bags ?? "—"}
              </span>
            </div>
          </div>
        );
      })}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() =>
          setOuts((o) => [
            ...o,
            { category: "CATEGORY_2", quantity_kg: "", bag_weight_kg: "25" },
          ])
        }
      >
        + Add category
      </Button>
      <ErrorNote message={msg(record.error)} />
      <div>
        <Button type="submit" disabled={record.isPending}>
          {record.isPending ? "Saving…" : "Record production"}
        </Button>
      </div>
    </form>
  );
}

export default function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: batch, isLoading, isError } = useBatch(id);
  const start = useStartBatch(id);
  const complete = useCompleteBatch(id);
  const can = useHasPermission();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }
  if (isError || !batch) return <ErrorNote message="Batch not found." />;

  const canMill = can("milling.batch.create");

  return (
    <div className="space-y-6">
      <div>
        <Link href="/milling" className="text-sm text-primary hover:underline">
          ← Back to milling
        </Link>
        <div className="mt-2 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{batch.reference}</h1>
          <StatusPill status={batch.status} />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Paddy inputs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          {batch.inputs.map((inp) => (
            <div
              key={inp.id}
              className="flex justify-between border-b border-border pb-1 last:border-0"
            >
              <span className="font-mono text-xs">
                {inp.paddy_lot_id.slice(0, 8)}…
              </span>
              <span>{formatKg(inp.quantity_kg)}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Next action</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {batch.status === "DRAFT" ? (
            canMill ? (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  Starting consumes the paddy above from stock.
                </p>
                <Button
                  onClick={() => start.mutate()}
                  disabled={start.isPending}
                >
                  {start.isPending
                    ? "Starting…"
                    : "Start batch (consume paddy)"}
                </Button>
                <ErrorNote message={msg(start.error)} />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Awaiting start.</p>
            )
          ) : null}

          {batch.status === "IN_PROGRESS" && canMill ? (
            <>
              <ProductionForm batchId={id} />
              <div className="border-t border-border pt-4">
                <Button
                  variant="outline"
                  onClick={() => complete.mutate()}
                  disabled={complete.isPending}
                >
                  {complete.isPending ? "Completing…" : "Complete batch"}
                </Button>
                <ErrorNote message={msg(complete.error)} />
              </div>
            </>
          ) : null}

          {batch.status === "COMPLETED" ? (
            <p className="text-sm text-green-700">Batch completed.</p>
          ) : null}
        </CardContent>
      </Card>

      {batch.productions.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Production outputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {batch.productions.map((prod) => (
              <div key={prod.id}>
                <p className="font-medium">{prod.reference}</p>
                {prod.outputs.map((o) => (
                  <div
                    key={o.id}
                    className="flex justify-between border-b border-border py-1 last:border-0"
                  >
                    <span>{o.category.replace("_", " ")}</span>
                    <span>
                      {formatKg(o.quantity_kg)} · {o.bag_count} bags
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
