"use client";

import { formatKg } from "@/lib/format";
import { useRiceLots } from "@/lib/rice";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/misc";

export default function RiceStockPage() {
  const { data, isLoading, isError } = useRiceLots();
  const lots = data?.items ?? [];
  const total = lots.reduce((sum, l) => sum + Number(l.available_kg), 0);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Rice Stock</h1>
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
        <ErrorNote message="Could not load rice stock." />
      ) : lots.length === 0 ? (
        <EmptyState>
          No rice lots yet. Pass a rice QC to create stock.
        </EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Lot</th>
                  <th className="p-3 font-medium">Category</th>
                  <th className="p-3 font-medium">Produced</th>
                  <th className="p-3 font-medium">Available</th>
                  <th className="p-3 font-medium">Bags</th>
                </tr>
              </thead>
              <tbody>
                {lots.map((lot) => (
                  <tr
                    key={lot.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-medium">{lot.reference}</td>
                    <td className="p-3">{lot.category.replace("_", " ")}</td>
                    <td className="p-3">{formatKg(lot.quantity_kg)}</td>
                    <td className="p-3">{formatKg(lot.available_kg)}</td>
                    <td className="p-3">{lot.bag_count}</td>
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
