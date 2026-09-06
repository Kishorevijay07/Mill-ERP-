"use client";

import { usePaddyLots } from "@/lib/milling";
import { formatKg } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/misc";

export default function PaddyStockPage() {
  const { data, isLoading, isError } = usePaddyLots();
  const lots = data?.items ?? [];
  const total = lots.reduce((sum, l) => sum + Number(l.available_kg), 0);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Paddy Stock</h1>
        <p className="text-sm text-muted-foreground">
          Total available:{" "}
          <span className="font-medium text-foreground">{formatKg(total)}</span>
        </p>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load paddy stock." />
      ) : lots.length === 0 ? (
        <EmptyState>
          No paddy lots yet. Accept a government load to create stock.
        </EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Lot</th>
                  <th className="p-3 font-medium">Received</th>
                  <th className="p-3 font-medium">Available</th>
                </tr>
              </thead>
              <tbody>
                {lots.map((lot) => (
                  <tr
                    key={lot.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{lot.reference}</td>
                    <td className="p-3">{formatKg(lot.quantity_kg)}</td>
                    <td className="p-3">{formatKg(lot.available_kg)}</td>
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
