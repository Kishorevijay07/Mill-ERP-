"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import {
  downloadInvoice,
  useApproveClaim,
  useClaim,
  useGenerateInvoice,
  useRecordPayment,
  useReplaceLines,
  useSubmitClaim,
} from "@/lib/billing";
import { formatMoney } from "@/lib/format";
import type { ClaimDetail } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ErrorNote, Spinner, StatusPill } from "@/components/ui/misc";

function msg(e: unknown): string | undefined {
  return e instanceof ApiError ? e.message : undefined;
}

type LineRow = {
  description: string;
  quantity: string;
  rate: string;
  is_deduction: boolean;
};

function LinesEditor({ claim }: { claim: ClaimDetail }) {
  const replace = useReplaceLines(claim.id);
  const [rows, setRows] = useState<LineRow[]>(
    claim.lines.map((l) => ({
      description: l.description,
      quantity: l.quantity,
      rate: l.rate,
      is_deduction: l.is_deduction,
    })),
  );

  function update(i: number, patch: Partial<LineRow>) {
    setRows((r) =>
      r.map((row, idx) => (idx === i ? { ...row, ...patch } : row)),
    );
  }

  return (
    <div className="space-y-3">
      {rows.map((row, i) => (
        <div key={i} className="grid gap-2 sm:grid-cols-12">
          <Input
            className="sm:col-span-5"
            placeholder="Description"
            value={row.description}
            onChange={(e) => update(i, { description: e.target.value })}
          />
          <Input
            className="sm:col-span-2"
            type="number"
            step="0.001"
            placeholder="Qty"
            value={row.quantity}
            onChange={(e) => update(i, { quantity: e.target.value })}
          />
          <Input
            className="sm:col-span-2"
            type="number"
            step="0.0001"
            placeholder="Rate"
            value={row.rate}
            onChange={(e) => update(i, { rate: e.target.value })}
          />
          <label className="flex items-center gap-1 text-xs sm:col-span-2">
            <input
              type="checkbox"
              checked={row.is_deduction}
              onChange={(e) => update(i, { is_deduction: e.target.checked })}
            />
            Deduction
          </label>
          <button
            type="button"
            className="text-xs text-red-600 sm:col-span-1"
            onClick={() => setRows((r) => r.filter((_, idx) => idx !== i))}
          >
            Remove
          </button>
        </div>
      ))}
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            setRows((r) => [
              ...r,
              {
                description: "",
                quantity: "0",
                rate: "0",
                is_deduction: false,
              },
            ])
          }
        >
          + Add line
        </Button>
        <Button
          size="sm"
          onClick={() => replace.mutate(rows)}
          disabled={replace.isPending}
        >
          {replace.isPending ? "Saving…" : "Save lines"}
        </Button>
      </div>
      <ErrorNote message={msg(replace.error)} />
    </div>
  );
}

function PaymentPanel({ claim }: { claim: ClaimDetail }) {
  const record = useRecordPayment(claim.id);
  const [amount, setAmount] = useState("");
  const [ref, setRef] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    record.mutate(
      { amount, reference_no: ref || undefined },
      {
        onSuccess: () => {
          setAmount("");
          setRef("");
        },
      },
    );
  }

  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-3">
      <Field label="Amount">
        <Input
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
      </Field>
      <Field label="Reference no (optional)">
        <Input value={ref} onChange={(e) => setRef(e.target.value)} />
      </Field>
      <div className="flex items-end">
        <Button type="submit" disabled={record.isPending}>
          {record.isPending ? "Recording…" : "Record payment"}
        </Button>
      </div>
      <div className="sm:col-span-3">
        <ErrorNote message={msg(record.error)} />
      </div>
    </form>
  );
}

export default function ClaimDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: claim, isLoading, isError } = useClaim(id);
  const submit = useSubmitClaim(id);
  const approve = useApproveClaim(id);
  const invoice = useGenerateInvoice(id);
  const can = useHasPermission();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }
  if (isError || !claim) return <ErrorNote message="Claim not found." />;

  const cur = claim.currency;
  const canBill = can("billing.create");

  async function handleInvoice() {
    const doc = await invoice.mutateAsync();
    await downloadInvoice(doc.document_id, doc.filename);
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/claims" className="text-sm text-primary hover:underline">
          ← Back to claims
        </Link>
        <div className="mt-2 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{claim.reference}</h1>
          <StatusPill status={claim.status} />
        </div>
      </div>

      <Card>
        <CardContent className="grid gap-4 text-sm sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase text-muted-foreground">Gross</p>
            <p className="mt-0.5 text-lg font-semibold">
              {formatMoney(claim.gross_amount, cur)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase text-muted-foreground">
              Deductions
            </p>
            <p className="mt-0.5 text-lg font-semibold">
              {formatMoney(claim.deduction_amount, cur)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase text-muted-foreground">
              Net payable
            </p>
            <p className="mt-0.5 text-lg font-semibold">
              {formatMoney(claim.net_amount, cur)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase text-muted-foreground">Paid</p>
            <p className="mt-0.5">{formatMoney(claim.paid_amount, cur)}</p>
          </div>
          <div>
            <p className="text-xs uppercase text-muted-foreground">
              Outstanding
            </p>
            <p className="mt-0.5 font-medium">
              {formatMoney(claim.outstanding_amount, cur)}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Charge lines</CardTitle>
        </CardHeader>
        <CardContent>
          {claim.status === "DRAFT" && canBill ? (
            <LinesEditor claim={claim} />
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="py-2 font-medium">Description</th>
                  <th className="py-2 font-medium">Qty</th>
                  <th className="py-2 font-medium">Rate</th>
                  <th className="py-2 text-right font-medium">Amount</th>
                </tr>
              </thead>
              <tbody>
                {claim.lines.map((l) => (
                  <tr
                    key={l.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="py-2">
                      {l.is_deduction ? "(-) " : ""}
                      {l.description}
                    </td>
                    <td className="py-2">{l.quantity}</td>
                    <td className="py-2">{l.rate}</td>
                    <td className="py-2 text-right">
                      {formatMoney((l.is_deduction ? "-" : "") + l.amount, cur)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {claim.status === "DRAFT" && can("billing.submit") ? (
            <Button onClick={() => submit.mutate()} disabled={submit.isPending}>
              Submit
            </Button>
          ) : null}
          {claim.status === "SUBMITTED" && can("billing.approve") ? (
            <Button
              onClick={() => approve.mutate()}
              disabled={approve.isPending}
            >
              Approve
            </Button>
          ) : null}
          {canBill ? (
            <Button
              variant="outline"
              onClick={handleInvoice}
              disabled={invoice.isPending}
            >
              {invoice.isPending
                ? "Generating…"
                : "Generate & download invoice"}
            </Button>
          ) : null}
        </CardContent>
      </Card>

      {claim.status === "APPROVED" || claim.status === "PARTIALLY_PAID" ? (
        can("payment.record") ? (
          <Card>
            <CardHeader>
              <CardTitle>Record payment</CardTitle>
            </CardHeader>
            <CardContent>
              <PaymentPanel claim={claim} />
            </CardContent>
          </Card>
        ) : null
      ) : null}

      {claim.payments.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Payment history</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {claim.payments.map((p) => (
              <div
                key={p.id}
                className="flex justify-between border-b border-border pb-1 last:border-0"
              >
                <span>
                  {p.reference}
                  {p.reference_no ? ` · ${p.reference_no}` : ""}
                </span>
                <span className="font-medium">
                  {formatMoney(p.amount, cur)}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
