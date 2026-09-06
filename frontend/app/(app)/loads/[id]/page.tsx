"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useHasPermission } from "@/lib/auth";
import { useArriveLoad, useLoad } from "@/lib/government";
import {
  useAcceptLoad,
  usePaddyLots,
  usePaddyQuality,
  useRecordQuality,
  useRecordWeighment,
  useRejectLoad,
  useWeighments,
} from "@/lib/receiving";
import type { GovernmentLoad, LoadStatus } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ErrorNote, Spinner, StatusBadge } from "@/components/ui/misc";

const STEPS: LoadStatus[] = [
  "DRAFT",
  "ARRIVED",
  "WEIGHED",
  "QC_PENDING",
  "ACCEPTED",
];

function apiMessage(error: unknown): string | undefined {
  return error instanceof ApiError ? error.message : undefined;
}

function Timeline({ status }: { status: LoadStatus }) {
  const currentIndex = STEPS.indexOf(status);
  const rejected = status === "REJECTED";
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {STEPS.map((step, i) => {
        const done = !rejected && i <= currentIndex;
        return (
          <span
            key={step}
            className={
              done
                ? "rounded-full bg-primary px-2.5 py-0.5 font-medium text-primary-foreground"
                : "rounded-full bg-muted px-2.5 py-0.5 text-muted-foreground"
            }
          >
            {step.replace("_", " ")}
          </span>
        );
      })}
      {rejected ? (
        <span className="rounded-full bg-red-100 px-2.5 py-0.5 font-medium text-red-700">
          REJECTED
        </span>
      ) : null}
    </div>
  );
}

function WeighmentForm({ loadId }: { loadId: string }) {
  const record = useRecordWeighment(loadId);
  const [gross, setGross] = useState("");
  const [tare, setTare] = useState("");
  const [ref, setRef] = useState("");

  const net =
    gross && tare && Number(gross) > Number(tare)
      ? (Number(gross) - Number(tare)).toFixed(3)
      : null;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    record.mutate({
      gross_kg: gross,
      tare_kg: tare,
      weighbridge_ref: ref || undefined,
    });
  }

  return (
    <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
      <Field label="Gross weight (kg)">
        <Input
          type="number"
          step="0.001"
          min="0"
          value={gross}
          onChange={(e) => setGross(e.target.value)}
          required
        />
      </Field>
      <Field label="Tare weight (kg)">
        <Input
          type="number"
          step="0.001"
          min="0"
          value={tare}
          onChange={(e) => setTare(e.target.value)}
          required
        />
      </Field>
      <div className="text-sm text-muted-foreground sm:col-span-2">
        Net weight:{" "}
        <span className="font-medium text-foreground">
          {net ? `${net} kg` : "—"}
        </span>
      </div>
      <Field label="Weighbridge ref (optional)" className="sm:col-span-2">
        <Input value={ref} onChange={(e) => setRef(e.target.value)} />
      </Field>
      <div className="space-y-2 sm:col-span-2">
        <ErrorNote message={apiMessage(record.error)} />
        <Button type="submit" disabled={record.isPending}>
          {record.isPending ? "Saving…" : "Record weighment"}
        </Button>
      </div>
    </form>
  );
}

function QualityForm({ loadId }: { loadId: string }) {
  const record = useRecordQuality(loadId);
  const [moisture, setMoisture] = useState("");
  const [foreign, setForeign] = useState("");
  const [damaged, setDamaged] = useState("");
  const [notes, setNotes] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    record.mutate({
      moisture_pct: moisture,
      foreign_matter_pct: foreign,
      damaged_pct: damaged,
      notes: notes || undefined,
    });
  }

  return (
    <form onSubmit={submit} className="grid gap-4 sm:grid-cols-3">
      <Field label="Moisture %">
        <Input
          type="number"
          step="0.01"
          min="0"
          max="100"
          value={moisture}
          onChange={(e) => setMoisture(e.target.value)}
          required
        />
      </Field>
      <Field label="Foreign matter %">
        <Input
          type="number"
          step="0.01"
          min="0"
          max="100"
          value={foreign}
          onChange={(e) => setForeign(e.target.value)}
          required
        />
      </Field>
      <Field label="Damaged %">
        <Input
          type="number"
          step="0.01"
          min="0"
          max="100"
          value={damaged}
          onChange={(e) => setDamaged(e.target.value)}
          required
        />
      </Field>
      <Field label="Notes (optional)" className="sm:col-span-3">
        <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
      </Field>
      <div className="space-y-2 sm:col-span-3">
        <ErrorNote message={apiMessage(record.error)} />
        <Button type="submit" disabled={record.isPending}>
          {record.isPending ? "Saving…" : "Record paddy quality"}
        </Button>
      </div>
    </form>
  );
}

function AcceptReject({ loadId }: { loadId: string }) {
  const accept = useAcceptLoad(loadId);
  const reject = useRejectLoad(loadId);
  const [reason, setReason] = useState("");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => accept.mutate()} disabled={accept.isPending}>
          {accept.isPending ? "Accepting…" : "Accept load"}
        </Button>
        <Button
          variant="destructive"
          onClick={() => reject.mutate(reason || undefined)}
          disabled={reject.isPending}
        >
          {reject.isPending ? "Rejecting…" : "Reject load"}
        </Button>
      </div>
      <Field label="Rejection reason (optional)">
        <Input value={reason} onChange={(e) => setReason(e.target.value)} />
      </Field>
      <ErrorNote
        message={apiMessage(accept.error) ?? apiMessage(reject.error)}
      />
    </div>
  );
}

function ActionPanel({ load }: { load: GovernmentLoad }) {
  const can = useHasPermission();
  const arrive = useArriveLoad();

  switch (load.status) {
    case "DRAFT":
      return can("government.load.create") ? (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Mark the load as arrived at the gate to begin receiving.
          </p>
          <Button
            onClick={() => arrive.mutate(load.id)}
            disabled={arrive.isPending}
          >
            {arrive.isPending ? "Updating…" : "Mark arrived"}
          </Button>
          <ErrorNote message={apiMessage(arrive.error)} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Waiting for arrival.</p>
      );
    case "ARRIVED":
    case "WEIGHED":
      // Allow (re)weighing at ARRIVED/WEIGHED, then QC once weighed.
      return (
        <div className="space-y-6">
          {can("receiving.weighment.record") ? (
            <div>
              <h3 className="mb-2 text-sm font-semibold">Weighment</h3>
              <WeighmentForm loadId={load.id} />
            </div>
          ) : null}
          {load.status === "WEIGHED" &&
          can("receiving.paddy_quality.record") ? (
            <div>
              <h3 className="mb-2 text-sm font-semibold">Paddy quality</h3>
              <QualityForm loadId={load.id} />
            </div>
          ) : null}
        </div>
      );
    case "QC_PENDING":
      return can("government.load.accept") ? (
        <AcceptReject loadId={load.id} />
      ) : (
        <p className="text-sm text-muted-foreground">
          Awaiting acceptance decision.
        </p>
      );
    case "ACCEPTED":
      return <AcceptedPanel loadId={load.id} />;
    case "REJECTED":
      return (
        <p className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          This load was rejected. No paddy stock was created.
        </p>
      );
    default:
      return null;
  }
}

function AcceptedPanel({ loadId }: { loadId: string }) {
  const { data } = usePaddyLots();
  const lot = data?.items.find((l) => l.load_id === loadId);
  return (
    <div className="rounded-md border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800">
      <p className="font-medium">Load accepted — paddy lot created.</p>
      {lot ? (
        <p className="mt-1">
          {lot.reference}: {lot.quantity_kg} kg received · {lot.available_kg} kg
          available
        </p>
      ) : null}
    </div>
  );
}

export default function LoadDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { data: load, isLoading, isError } = useLoad(id);
  const { data: weighments } = useWeighments(id);
  const qualityEnabled =
    !!load && ["QC_PENDING", "ACCEPTED", "REJECTED"].includes(load.status);
  const { data: quality } = usePaddyQuality(id, qualityEnabled);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }
  if (isError || !load) {
    return <ErrorNote message="Load not found." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/loads" className="text-sm text-primary hover:underline">
          ← Back to loads
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">{load.reference}</h1>
          <StatusBadge status={load.status} />
        </div>
      </div>

      <Card>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Detail label="Lorry number" value={load.lorry_number} />
          <Detail label="Driver" value={load.driver_name ?? "—"} />
          <Detail
            label="Declared quantity"
            value={
              load.declared_quantity_kg
                ? `${load.declared_quantity_kg} kg`
                : "—"
            }
          />
          <Detail
            label="Created"
            value={new Date(load.created_at).toLocaleString()}
          />
          <div className="sm:col-span-2">
            <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">
              Progress
            </p>
            <Timeline status={load.status} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Next action</CardTitle>
        </CardHeader>
        <CardContent>
          <ActionPanel load={load} />
        </CardContent>
      </Card>

      {weighments && weighments.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Weighments</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {weighments.map((w) => (
              <div
                key={w.id}
                className="flex flex-wrap justify-between gap-2 border-b border-border pb-2 last:border-0 last:pb-0"
              >
                <span>
                  Gross {w.gross_kg} − Tare {w.tare_kg} ={" "}
                  <span className="font-medium">{w.net_kg} kg</span>
                </span>
                {w.is_final ? (
                  <span className="text-xs font-medium text-primary">
                    FINAL
                  </span>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    superseded
                  </span>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {quality ? (
        <Card>
          <CardHeader>
            <CardTitle>Paddy quality</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 text-sm sm:grid-cols-3">
            <Detail label="Moisture" value={`${quality.moisture_pct}%`} />
            <Detail
              label="Foreign matter"
              value={`${quality.foreign_matter_pct}%`}
            />
            <Detail label="Damaged" value={`${quality.damaged_pct}%`} />
            {quality.notes ? (
              <div className="sm:col-span-3">
                <Detail label="Notes" value={quality.notes} />
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-muted-foreground">
        {label}
      </p>
      <p className="mt-0.5">{value}</p>
    </div>
  );
}
