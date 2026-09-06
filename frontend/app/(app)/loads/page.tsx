"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { useCreateLoad, useDeliveryOrders, useLoads } from "@/lib/government";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import {
  EmptyState,
  ErrorNote,
  Spinner,
  StatusBadge,
} from "@/components/ui/misc";

function NewLoadForm({ onClose }: { onClose: () => void }) {
  const { data: dos } = useDeliveryOrders();
  const createLoad = useCreateLoad();
  const [deliveryOrderId, setDeliveryOrderId] = useState("");
  const [lorry, setLorry] = useState("");
  const [driver, setDriver] = useState("");
  const [declared, setDeclared] = useState("");

  const orders = dos?.items ?? [];

  function submit(e: React.FormEvent) {
    e.preventDefault();
    createLoad.mutate(
      {
        delivery_order_id: deliveryOrderId,
        lorry_number: lorry,
        driver_name: driver || undefined,
        declared_quantity_kg: declared || undefined,
      },
      { onSuccess: onClose },
    );
  }

  const errorMessage =
    createLoad.error instanceof ApiError ? createLoad.error.message : undefined;

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>New government load</CardTitle>
      </CardHeader>
      <CardContent>
        {orders.length === 0 ? (
          <EmptyState>
            No delivery orders yet. Create one under{" "}
            <Link href="/setup" className="font-medium text-primary underline">
              Setup
            </Link>{" "}
            first.
          </EmptyState>
        ) : (
          <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
            <Field label="Delivery order" className="sm:col-span-2">
              <Select
                value={deliveryOrderId}
                onChange={(e) => setDeliveryOrderId(e.target.value)}
                required
              >
                <option value="" disabled>
                  Select a delivery order
                </option>
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.reference} · DO {o.do_number} · {o.quantity_kg} kg
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Lorry number">
              <Input
                value={lorry}
                onChange={(e) => setLorry(e.target.value)}
                required
              />
            </Field>
            <Field label="Driver name (optional)">
              <Input
                value={driver}
                onChange={(e) => setDriver(e.target.value)}
              />
            </Field>
            <Field label="Declared quantity (kg, optional)">
              <Input
                type="number"
                step="0.001"
                min="0"
                value={declared}
                onChange={(e) => setDeclared(e.target.value)}
              />
            </Field>
            <div className="flex items-end gap-2">
              <Button
                type="submit"
                disabled={createLoad.isPending || !deliveryOrderId}
              >
                {createLoad.isPending ? "Creating…" : "Create load"}
              </Button>
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
            </div>
            <div className="sm:col-span-2">
              <ErrorNote message={errorMessage} />
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

export default function LoadsPage() {
  const { data, isLoading, isError } = useLoads();
  const [creating, setCreating] = useState(false);
  const can = useHasPermission();

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Government Loads</h1>
          <p className="text-sm text-muted-foreground">
            Receiving workflow: arrive → weigh → QC → accept.
          </p>
        </div>
        {can("government.load.create") && !creating ? (
          <Button onClick={() => setCreating(true)}>New load</Button>
        ) : null}
      </div>

      {creating ? <NewLoadForm onClose={() => setCreating(false)} /> : null}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load records." />
      ) : !data || data.items.length === 0 ? (
        <EmptyState>No government loads yet.</EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Reference</th>
                  <th className="p-3 font-medium">Lorry</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Created</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {data.items.map((load) => (
                  <tr
                    key={load.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{load.reference}</td>
                    <td className="p-3">{load.lorry_number}</td>
                    <td className="p-3">
                      <StatusBadge status={load.status} />
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {new Date(load.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        href={`/loads/${load.id}`}
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
