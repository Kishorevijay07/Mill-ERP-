import type { LoadStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent",
        className,
      )}
      role="status"
      aria-label="Loading"
    />
  );
}

const STATUS_STYLES: Record<LoadStatus, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  ARRIVED: "bg-blue-100 text-blue-700",
  WEIGHED: "bg-indigo-100 text-indigo-700",
  QC_PENDING: "bg-amber-100 text-amber-800",
  ACCEPTED: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
};

export function StatusBadge({ status }: { status: LoadStatus }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_STYLES[status],
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}

const PILL_STYLES: Record<string, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  ARRIVED: "bg-blue-100 text-blue-700",
  WEIGHED: "bg-indigo-100 text-indigo-700",
  QC_PENDING: "bg-amber-100 text-amber-800",
  PENDING: "bg-amber-100 text-amber-800",
  IN_PROGRESS: "bg-indigo-100 text-indigo-700",
  PREPARED: "bg-indigo-100 text-indigo-700",
  DISPATCHED: "bg-blue-100 text-blue-700",
  SUBMITTED: "bg-blue-100 text-blue-700",
  APPROVED: "bg-teal-100 text-teal-700",
  PARTIALLY_PAID: "bg-amber-100 text-amber-800",
  ACCEPTED: "bg-green-100 text-green-700",
  COMPLETED: "bg-green-100 text-green-700",
  PASSED: "bg-green-100 text-green-700",
  DELIVERED: "bg-green-100 text-green-700",
  PAID: "bg-green-100 text-green-700",
  REJECTED: "bg-red-100 text-red-700",
  FAILED: "bg-red-100 text-red-700",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
        PILL_STYLES[status] ?? "bg-muted text-muted-foreground",
      )}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function ErrorNote({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
      {message}
    </p>
  );
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
      {children}
    </div>
  );
}
