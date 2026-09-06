"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { formatMoney } from "@/lib/format";
import {
  useChargeRates,
  useCreateChargeRate,
  useDeleteChargeRate,
  useMillSettings,
  useUpdateMillSettings,
} from "@/lib/settings";
import type { ChargeUnit } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/misc";

function msg(e: unknown): string | undefined {
  return e instanceof ApiError ? e.message : undefined;
}

function MillProfile({ canManage }: { canManage: boolean }) {
  const { data, isLoading } = useMillSettings();
  const update = useUpdateMillSettings();
  const [form, setForm] = useState({
    name: "",
    address: "",
    registration_no: "",
    currency: "INR",
    invoice_notes: "",
  });

  useEffect(() => {
    if (data) {
      setForm({
        name: data.name,
        address: data.address ?? "",
        registration_no: data.registration_no ?? "",
        currency: data.currency,
        invoice_notes: data.invoice_notes ?? "",
      });
    }
  }, [data]);

  if (isLoading) return <Spinner />;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    update.mutate(form);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mill profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
          <Field label="Mill name">
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              disabled={!canManage}
              required
            />
          </Field>
          <Field label="Currency">
            <Input
              value={form.currency}
              onChange={(e) => setForm({ ...form, currency: e.target.value })}
              disabled={!canManage}
            />
          </Field>
          <Field label="Address" className="sm:col-span-2">
            <Input
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              disabled={!canManage}
            />
          </Field>
          <Field label="Registration no">
            <Input
              value={form.registration_no}
              onChange={(e) =>
                setForm({ ...form, registration_no: e.target.value })
              }
              disabled={!canManage}
            />
          </Field>
          <Field label="Invoice notes" className="sm:col-span-2">
            <Input
              value={form.invoice_notes}
              onChange={(e) =>
                setForm({ ...form, invoice_notes: e.target.value })
              }
              disabled={!canManage}
            />
          </Field>
          {canManage ? (
            <div className="sm:col-span-2">
              <ErrorNote message={msg(update.error)} />
              <Button
                type="submit"
                disabled={update.isPending}
                className="mt-2"
              >
                {update.isPending ? "Saving…" : "Save profile"}
              </Button>
            </div>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}

function ChargeRates({ canManage }: { canManage: boolean }) {
  const { data, isLoading } = useChargeRates();
  const create = useCreateChargeRate();
  const remove = useDeleteChargeRate();
  const [form, setForm] = useState({
    code: "",
    label: "",
    rate: "",
    unit: "PER_KG" as ChargeUnit,
    is_deduction: false,
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { ...form, is_active: true },
      {
        onSuccess: () =>
          setForm({
            code: "",
            label: "",
            rate: "",
            unit: "PER_KG",
            is_deduction: false,
          }),
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Charge rates</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <Spinner />
        ) : (data?.length ?? 0) === 0 ? (
          <EmptyState>No charge rates configured.</EmptyState>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-muted-foreground">
              <tr>
                <th className="py-2 font-medium">Code</th>
                <th className="py-2 font-medium">Label</th>
                <th className="py-2 font-medium">Rate</th>
                <th className="py-2 font-medium">Unit</th>
                <th className="py-2 font-medium">Type</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((r) => (
                <tr key={r.id} className="border-b border-border last:border-0">
                  <td className="py-2 font-medium">{r.code}</td>
                  <td className="py-2">{r.label}</td>
                  <td className="py-2">{formatMoney(r.rate)}</td>
                  <td className="py-2">{r.unit}</td>
                  <td className="py-2">
                    {r.is_deduction ? "Deduction" : "Charge"}
                  </td>
                  <td className="py-2 text-right">
                    {canManage ? (
                      <button
                        type="button"
                        className="text-xs text-red-600"
                        onClick={() => remove.mutate(r.id)}
                      >
                        Delete
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {canManage ? (
          <form
            onSubmit={submit}
            className="grid gap-3 border-t border-border pt-4 sm:grid-cols-5"
          >
            <Field label="Code">
              <Input
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
                required
              />
            </Field>
            <Field label="Label" className="sm:col-span-2">
              <Input
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
                required
              />
            </Field>
            <Field label="Rate">
              <Input
                type="number"
                step="0.0001"
                min="0"
                value={form.rate}
                onChange={(e) => setForm({ ...form, rate: e.target.value })}
                required
              />
            </Field>
            <Field label="Unit">
              <Select
                value={form.unit}
                onChange={(e) =>
                  setForm({ ...form, unit: e.target.value as ChargeUnit })
                }
              >
                <option value="PER_KG">Per kg</option>
                <option value="PER_QUINTAL">Per quintal</option>
                <option value="FLAT">Flat</option>
              </Select>
            </Field>
            <label className="flex items-center gap-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                checked={form.is_deduction}
                onChange={(e) =>
                  setForm({ ...form, is_deduction: e.target.checked })
                }
              />
              Deduction
            </label>
            <div className="sm:col-span-3">
              <ErrorNote message={msg(create.error)} />
              <Button
                type="submit"
                disabled={create.isPending}
                className="mt-1"
              >
                {create.isPending ? "Adding…" : "Add rate"}
              </Button>
            </div>
          </form>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  const can = useHasPermission();
  const canManage = can("settings.manage");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <MillProfile canManage={canManage} />
      <ChargeRates canManage={canManage} />
    </div>
  );
}
