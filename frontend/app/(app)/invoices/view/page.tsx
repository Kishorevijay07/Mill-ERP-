"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useRef, useState } from "react";
import { useHasPermission } from "@/lib/auth";
import { formatDate, formatMoney } from "@/lib/format";
import {
  downloadInvoicePdf,
  useInvoice,
  useIssueInvoice,
  useUploadEwayBill,
} from "@/lib/invoicing";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorNote, Spinner, StatusPill } from "@/components/ui/misc";

function Detail({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm">{value || "—"}</p>
    </div>
  );
}

function InvoiceView() {
  const id = useSearchParams().get("id") ?? "";
  const { data: inv, isLoading, isError } = useInvoice(id);
  const issue = useIssueInvoice(id);
  const uploadEway = useUploadEwayBill(id);
  const can = useHasPermission();
  const fileInput = useRef<HTMLInputElement>(null);
  const [downloadError, setDownloadError] = useState<string | undefined>();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }
  if (isError || !inv) {
    return <ErrorNote message="Could not load invoice." />;
  }

  async function onDownload() {
    setDownloadError(undefined);
    try {
      await downloadInvoicePdf(inv!.id, inv!.invoice_number);
    } catch {
      setDownloadError("Failed to download the invoice PDF.");
    }
  }

  return (
    <div className="space-y-6">
      <Link href="/invoices" className="text-sm text-primary hover:underline">
        ← Back to invoices
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">
            Invoice {inv.invoice_number}
          </h1>
          <StatusPill status={inv.status} />
        </div>
        <div className="flex flex-wrap gap-2">
          {inv.status === "DRAFT" && can("invoice.issue") ? (
            <Button onClick={() => issue.mutate()} disabled={issue.isPending}>
              {issue.isPending ? "Issuing…" : "Issue invoice"}
            </Button>
          ) : null}
          <Button variant="outline" onClick={onDownload}>
            Download PDF
          </Button>
          {can("invoice.create") ? (
            <>
              <input
                ref={fileInput}
                type="file"
                accept="application/pdf"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) uploadEway.mutate(f);
                  e.target.value = "";
                }}
              />
              <Button
                variant="outline"
                onClick={() => fileInput.current?.click()}
                disabled={uploadEway.isPending}
              >
                {uploadEway.isPending
                  ? "Uploading…"
                  : inv.eway_document_id
                    ? "Replace e-Way Bill"
                    : "Upload e-Way Bill"}
              </Button>
            </>
          ) : null}
        </div>
      </div>
      <ErrorNote message={downloadError} />

      <Card>
        <CardHeader>
          <CardTitle>Buyer & dispatch</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <Detail label="Buyer" value={inv.buyer_name} />
          <Detail label="GSTIN/UIN" value={inv.buyer_gstin} />
          <Detail label="Invoice date" value={formatDate(inv.invoice_date)} />
          <Detail label="Address" value={inv.buyer_address} />
          <Detail label="Destination" value={inv.destination} />
          <Detail label="Motor vehicle no" value={inv.motor_vehicle_no} />
          <Detail label="Dispatched through" value={inv.dispatched_through} />
          <Detail label="Delivery note" value={inv.delivery_note} />
          <Detail label="Remarks" value={inv.remarks} />
          <Detail
            label="e-Way Bill"
            value={inv.eway_document_id ? "Attached" : null}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Line items</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-muted-foreground">
              <tr>
                <th className="p-2 font-medium">Description</th>
                <th className="p-2 font-medium">HSN/SAC</th>
                <th className="p-2 font-medium">Qty</th>
                <th className="p-2 font-medium">Rate</th>
                <th className="p-2 font-medium">Taxable</th>
                {inv.is_interstate ? (
                  <th className="p-2 font-medium">IGST</th>
                ) : (
                  <>
                    <th className="p-2 font-medium">CGST</th>
                    <th className="p-2 font-medium">SGST</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {inv.lines.map((ln) => (
                <tr
                  key={ln.id}
                  className="border-b border-border last:border-0"
                >
                  <td className="whitespace-pre-line p-2">{ln.description}</td>
                  <td className="p-2">{ln.hsn_sac || "—"}</td>
                  <td className="p-2">
                    {ln.quantity} {ln.uom}
                  </td>
                  <td className="p-2">{formatMoney(ln.rate)}</td>
                  <td className="p-2">{formatMoney(ln.taxable_amount)}</td>
                  {inv.is_interstate ? (
                    <td className="p-2">
                      {formatMoney(ln.igst_amount)}
                      <span className="text-xs text-muted-foreground">
                        {" "}
                        @ {ln.igst_rate}%
                      </span>
                    </td>
                  ) : (
                    <>
                      <td className="p-2">
                        {formatMoney(ln.cgst_amount)}
                        <span className="text-xs text-muted-foreground">
                          {" "}
                          @ {ln.cgst_rate}%
                        </span>
                      </td>
                      <td className="p-2">
                        {formatMoney(ln.sgst_amount)}
                        <span className="text-xs text-muted-foreground">
                          {" "}
                          @ {ln.sgst_rate}%
                        </span>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-4 space-y-1 border-t border-border pt-4 text-sm sm:ml-auto sm:w-72">
            <div className="flex justify-between">
              <span>Taxable value</span>
              <span>{formatMoney(inv.taxable_amount)}</span>
            </div>
            {inv.is_interstate ? (
              <div className="flex justify-between">
                <span>IGST</span>
                <span>{formatMoney(inv.total_tax_amount)}</span>
              </div>
            ) : (
              <>
                <div className="flex justify-between">
                  <span>CGST</span>
                  <span>
                    {formatMoney(
                      inv.tax_summary
                        .reduce((s, r) => s + Number(r.cgst_amount), 0)
                        .toFixed(2),
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>SGST</span>
                  <span>
                    {formatMoney(
                      inv.tax_summary
                        .reduce((s, r) => s + Number(r.sgst_amount), 0)
                        .toFixed(2),
                    )}
                  </span>
                </div>
              </>
            )}
            <div className="flex justify-between font-semibold">
              <span>Grand total</span>
              <span>{formatMoney(inv.grand_total)}</span>
            </div>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            {inv.amount_in_words}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function InvoiceViewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      }
    >
      <InvoiceView />
    </Suspense>
  );
}
