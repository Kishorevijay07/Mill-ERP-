"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import {
  useCreateReceipt,
  useDispatch,
  useDispatchDispatch,
  usePrepareDispatch,
} from "@/lib/delivery";
import { formatKg } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ErrorNote, Spinner, StatusPill } from "@/components/ui/misc";

function msg(e: unknown): string | undefined {
  return e instanceof ApiError ? e.message : undefined;
}

function ReceiptForm({ dispatchId }: { dispatchId: string }) {
  const create = useCreateReceipt(dispatchId);
  const [received, setReceived] = useState("");
  const [bags, setBags] = useState("");
  const [number, setNumber] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate({
      received_quantity_kg: received,
      received_bags: bags ? Number(bags) : undefined,
      receipt_number: number || undefined,
    });
  }

  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-3">
      <Field label="Received quantity (kg)">
        <Input
          type="number"
          step="0.001"
          min="0"
          value={received}
          onChange={(e) => setReceived(e.target.value)}
          required
        />
      </Field>
      <Field label="Received bags (optional)">
        <Input
          type="number"
          min="0"
          value={bags}
          onChange={(e) => setBags(e.target.value)}
        />
      </Field>
      <Field label="Receipt number (optional)">
        <Input value={number} onChange={(e) => setNumber(e.target.value)} />
      </Field>
      <div className="space-y-2 sm:col-span-3">
        <ErrorNote message={msg(create.error)} />
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? "Saving…" : "Record delivery receipt"}
        </Button>
      </div>
    </form>
  );
}

export default function DispatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: dispatch, isLoading, isError } = useDispatch(id);
  const prepare = usePrepareDispatch(id);
  const dispatchNow = useDispatchDispatch(id);
  const can = useHasPermission();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }
  if (isError || !dispatch) return <ErrorNote message="Dispatch not found." />;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/dispatch" className="text-sm text-primary hover:underline">
          ← Back to dispatch
        </Link>
        <div className="mt-2 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{dispatch.reference}</h1>
          <StatusPill status={dispatch.status} />
        </div>
      </div>

      <Card>
        <CardContent className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">
              Destination
            </p>
            <p className="mt-0.5">{dispatch.destination_name}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">
              Lorry
            </p>
            <p className="mt-0.5">{dispatch.lorry_number}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rice lots</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          {dispatch.items.map((item) => (
            <div
              key={item.id}
              className="flex justify-between border-b border-border pb-1 last:border-0"
            >
              <span className="font-mono text-xs">
                {item.rice_lot_id.slice(0, 8)}…
              </span>
              <span>{formatKg(item.quantity_kg)}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Next action</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {dispatch.status === "DRAFT" ? (
            can("dispatch.create") ? (
              <>
                <Button
                  onClick={() => prepare.mutate()}
                  disabled={prepare.isPending}
                >
                  {prepare.isPending ? "Preparing…" : "Prepare dispatch"}
                </Button>
                <ErrorNote message={msg(prepare.error)} />
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Awaiting preparation.
              </p>
            )
          ) : null}

          {dispatch.status === "PREPARED" ? (
            can("dispatch.confirm") ? (
              <>
                <p className="text-sm text-muted-foreground">
                  Dispatching deducts the rice above from stock.
                </p>
                <Button
                  onClick={() => dispatchNow.mutate()}
                  disabled={dispatchNow.isPending}
                >
                  {dispatchNow.isPending
                    ? "Dispatching…"
                    : "Dispatch (deduct stock)"}
                </Button>
                <ErrorNote message={msg(dispatchNow.error)} />
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Awaiting dispatch confirmation.
              </p>
            )
          ) : null}

          {dispatch.status === "DISPATCHED" ? (
            can("dispatch.confirm") ? (
              <ReceiptForm dispatchId={id} />
            ) : (
              <p className="text-sm text-muted-foreground">
                Awaiting delivery receipt.
              </p>
            )
          ) : null}

          {dispatch.status === "DELIVERED" && dispatch.receipt ? (
            <div className="rounded-md border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800">
              <p className="font-medium">
                Delivered — {dispatch.receipt.reference}
              </p>
              <p className="mt-1">
                Dispatched {formatKg(dispatch.receipt.dispatched_quantity_kg)} ·
                Received {formatKg(dispatch.receipt.received_quantity_kg)} ·
                Shortage {formatKg(dispatch.receipt.shortage_kg)} · Excess{" "}
                {formatKg(dispatch.receipt.excess_kg)}
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
