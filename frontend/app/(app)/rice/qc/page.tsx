"use client";

import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import { useFailQuality, usePassQuality, useRiceQuality } from "@/lib/rice";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  EmptyState,
  ErrorNote,
  Spinner,
  StatusPill,
} from "@/components/ui/misc";

export default function RiceQcPage() {
  const { data, isLoading, isError } = useRiceQuality("PENDING");
  const pass = usePassQuality();
  const fail = useFailQuality();
  const can = useHasPermission();
  const canApprove = can("rice.qc.approve");
  const items = data?.items ?? [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Rice Quality Control</h1>
        <p className="text-sm text-muted-foreground">
          Passing QC creates a rice lot and adds it to stock.
        </p>
      </div>
      <ErrorNote
        message={
          pass.error instanceof ApiError ? pass.error.message : undefined
        }
      />
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="h-8 w-8" />
        </div>
      ) : isError ? (
        <ErrorNote message="Could not load QC queue." />
      ) : items.length === 0 ? (
        <EmptyState>No rice outputs pending QC.</EmptyState>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Output</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Created</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {items.map((q) => (
                  <tr
                    key={q.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="p-3 font-mono text-xs">
                      {q.output_id.slice(0, 8)}…
                    </td>
                    <td className="p-3">
                      <StatusPill status={q.status} />
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {formatDate(q.created_at)}
                    </td>
                    <td className="p-3 text-right">
                      {canApprove ? (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            onClick={() => pass.mutate(q.id)}
                            disabled={pass.isPending}
                          >
                            Pass
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => fail.mutate({ id: q.id })}
                            disabled={fail.isPending}
                          >
                            Fail
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          View only
                        </span>
                      )}
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
