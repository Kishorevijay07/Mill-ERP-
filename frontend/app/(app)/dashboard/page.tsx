"use client";

import { useDashboard } from "@/lib/dashboard";
import { formatKg, formatMoney } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorNote, Spinner } from "@/components/ui/misc";

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <p className="text-xs font-medium uppercase text-muted-foreground">
          {label}
        </p>
        <p className="mt-1 text-2xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data, isLoading, isError } = useDashboard();

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Dashboard</h1>
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError || !data ? (
        <ErrorNote message="Could not load dashboard." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Kpi
            label="Paddy received"
            value={formatKg(data.paddy_received_kg)}
          />
          <Kpi
            label="Paddy available"
            value={formatKg(data.paddy_available_kg)}
          />
          <Kpi label="Rice stock" value={formatKg(data.rice_stock_kg)} />
          <Kpi label="Pending delivery" value={String(data.pending_delivery)} />
          <Kpi label="Claims pending" value={String(data.claims_pending)} />
          <Kpi label="Amount paid" value={formatMoney(data.amount_paid)} />
          <Kpi
            label="Amount outstanding"
            value={formatMoney(data.amount_outstanding)}
          />
        </div>
      )}
    </div>
  );
}
