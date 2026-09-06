"use client";

import { useReceipts } from "@/lib/delivery";
import { formatDate, formatKg } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/misc";

export default function ReceiptsPage() {
  const { data, isLoading, isError } = useReceipts();
  const items = data?.items ?? [];

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Delivery Receipts</h1>
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load receipts." />
      ) : items.length === 0 ? (
        <EmptyState>No delivery receipts yet.</EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Receipt</th>
                  <th className="p-3 font-medium">Dispatched</th>
                  <th className="p-3 font-medium">Received</th>
                  <th className="p-3 font-medium">Shortage</th>
                  <th className="p-3 font-medium">Excess</th>
                  <th className="p-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{r.reference}</td>
                    <td className="p-3">
                      {formatKg(r.dispatched_quantity_kg)}
                    </td>
                    <td className="p-3">{formatKg(r.received_quantity_kg)}</td>
                    <td className="p-3">{formatKg(r.shortage_kg)}</td>
                    <td className="p-3">{formatKg(r.excess_kg)}</td>
                    <td className="p-3 text-muted-foreground">
                      {formatDate(r.created_at)}
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
