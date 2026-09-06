"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api";
import {
  useAgencies,
  useAllocations,
  useCreateAgency,
  useCreateAllocation,
  useCreateDeliveryOrder,
  useDeliveryOrders,
} from "@/lib/government";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, ErrorNote } from "@/components/ui/misc";

function apiMessage(error: unknown): string | undefined {
  return error instanceof ApiError ? error.message : undefined;
}

const today = () => new Date().toISOString().slice(0, 10);

function AgencySection() {
  const { data } = useAgencies();
  const create = useCreateAgency();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { code, name },
      {
        onSuccess: () => {
          setCode("");
          setName("");
        },
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>1 · Government agencies</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-3">
          <Field label="Code">
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          </Field>
          <Field label="Name" className="sm:col-span-2">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </Field>
          <div className="sm:col-span-3">
            <ErrorNote message={apiMessage(create.error)} />
            <Button type="submit" disabled={create.isPending} className="mt-2">
              {create.isPending ? "Saving…" : "Add agency"}
            </Button>
          </div>
        </form>
        <ItemList
          items={(data?.items ?? []).map((a) => `${a.code} — ${a.name}`)}
          empty="No agencies yet."
        />
      </CardContent>
    </Card>
  );
}

function AllocationSection() {
  const { data: agencies } = useAgencies();
  const { data } = useAllocations();
  const create = useCreateAllocation();
  const [agencyId, setAgencyId] = useState("");
  const [qty, setQty] = useState("");
  const [date, setDate] = useState(today());

  const options = agencies?.items ?? [];

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { agency_id: agencyId, quantity_kg: qty, allocated_on: date },
      { onSuccess: () => setQty("") },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>2 · Allocations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {options.length === 0 ? (
          <EmptyState>Add an agency first.</EmptyState>
        ) : (
          <form onSubmit={submit} className="grid gap-3 sm:grid-cols-3">
            <Field label="Agency">
              <Select
                value={agencyId}
                onChange={(e) => setAgencyId(e.target.value)}
                required
              >
                <option value="" disabled>
                  Select agency
                </option>
                {options.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.code} — {a.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Quantity (kg)">
              <Input
                type="number"
                step="0.001"
                min="0.001"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                required
              />
            </Field>
            <Field label="Allocated on">
              <Input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </Field>
            <div className="sm:col-span-3">
              <ErrorNote message={apiMessage(create.error)} />
              <Button
                type="submit"
                disabled={create.isPending || !agencyId}
                className="mt-2"
              >
                {create.isPending ? "Saving…" : "Add allocation"}
              </Button>
            </div>
          </form>
        )}
        <ItemList
          items={(data?.items ?? []).map(
            (a) => `${a.reference} — ${a.quantity_kg} kg`,
          )}
          empty="No allocations yet."
        />
      </CardContent>
    </Card>
  );
}

function DeliveryOrderSection() {
  const { data: allocations } = useAllocations();
  const { data } = useDeliveryOrders();
  const create = useCreateDeliveryOrder();
  const [allocationId, setAllocationId] = useState("");
  const [doNumber, setDoNumber] = useState("");
  const [qty, setQty] = useState("");
  const [date, setDate] = useState(today());

  const options = allocations?.items ?? [];

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      {
        allocation_id: allocationId,
        do_number: doNumber,
        quantity_kg: qty,
        issued_on: date,
      },
      {
        onSuccess: () => {
          setDoNumber("");
          setQty("");
        },
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>3 · Delivery orders</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {options.length === 0 ? (
          <EmptyState>Add an allocation first.</EmptyState>
        ) : (
          <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
            <Field label="Allocation" className="sm:col-span-2">
              <Select
                value={allocationId}
                onChange={(e) => setAllocationId(e.target.value)}
                required
              >
                <option value="" disabled>
                  Select allocation
                </option>
                {options.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.reference} — {a.quantity_kg} kg
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Govt DO number">
              <Input
                value={doNumber}
                onChange={(e) => setDoNumber(e.target.value)}
                required
              />
            </Field>
            <Field label="Quantity (kg)">
              <Input
                type="number"
                step="0.001"
                min="0.001"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                required
              />
            </Field>
            <Field label="Issued on">
              <Input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </Field>
            <div className="sm:col-span-2">
              <ErrorNote message={apiMessage(create.error)} />
              <Button
                type="submit"
                disabled={create.isPending || !allocationId}
                className="mt-2"
              >
                {create.isPending ? "Saving…" : "Add delivery order"}
              </Button>
            </div>
          </form>
        )}
        <ItemList
          items={(data?.items ?? []).map(
            (o) => `${o.reference} — DO ${o.do_number} — ${o.quantity_kg} kg`,
          )}
          empty="No delivery orders yet."
        />
      </CardContent>
    </Card>
  );
}

function ItemList({ items, empty }: { items: string[]; empty: string }) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{empty}</p>;
  }
  return (
    <ul className="space-y-1 text-sm">
      {items.map((it, i) => (
        <li key={i} className="rounded-md bg-muted px-3 py-1.5">
          {it}
        </li>
      ))}
    </ul>
  );
}

export default function SetupPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Setup</h1>
        <p className="text-sm text-muted-foreground">
          Create the government chain that loads are received against.
        </p>
      </div>
      <AgencySection />
      <AllocationSection />
      <DeliveryOrderSection />
    </div>
  );
}
