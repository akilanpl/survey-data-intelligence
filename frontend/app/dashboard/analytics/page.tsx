"use client";

import { useQuery } from "@tanstack/react-query";
import { Clock3 } from "lucide-react";
import { DetectorDistributionChart } from "@/components/DetectorDistributionChart";
import { EnumeratorComparisonChart } from "@/components/EnumeratorComparisonChart";
import { GeographicComparisonChart } from "@/components/GeographicComparisonChart";
import { TemporalTrendChart } from "@/components/TemporalTrendChart";
import { BatchSelectionGate } from "@/components/shell";
import { EmptyState, ErrorState } from "@/components/status";
import { getDetectorAnalytics, getExplorer, getTemporalAnalytics } from "@/lib/api";

export default function AnalyticsPage() {
  return (
    <BatchSelectionGate emptyDetail="Ingest data before analytics.">
      {(batchId) => <AnalyticsInner batchId={batchId} />}
    </BatchSelectionGate>
  );
}

function ChartSkeleton() {
  return (
    <div className="space-y-2" role="status" aria-live="polite">
      <div className="sv-skeleton h-80 w-full" />
    </div>
  );
}

function AnalyticsInner({ batchId }: { batchId: string }) {
  const temporal = useQuery({
    queryKey: ["temporal", batchId],
    queryFn: () => getTemporalAnalytics(batchId),
    retry: false,
  });
  const detectors = useQuery({
    queryKey: ["detector-analytics", batchId],
    queryFn: () => getDetectorAnalytics(batchId),
    retry: false,
  });
  const explorer = useQuery({
    queryKey: ["explorer", batchId],
    queryFn: () => getExplorer({ batch_id: batchId, variable: "employment_rate", level: "district" }),
    retry: false,
  });
  const enumerators = useQuery({
    queryKey: ["explorer-enumerators", batchId],
    queryFn: () => getExplorer({ batch_id: batchId, variable: "employment_rate", level: "enumerator" }),
    retry: false,
  });

  if (temporal.isPending && detectors.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader batchId={batchId} />
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    );
  }
  if (temporal.isError && detectors.isError && explorer.isError) {
    return (
      <ErrorState
        message="Analytics could not be loaded."
        onRetry={() => {
          temporal.refetch();
          detectors.refetch();
          explorer.refetch();
          enumerators.refetch();
        }}
      />
    );
  }

  const detectorPayload = detectors.data as { available?: boolean; items?: { detector: string; count: number }[]; message?: string } | undefined;
  const temporalPayload = temporal.data as {
    available?: boolean;
    items?: { period: string; observed: number | null; baseline: number | null; threshold?: number | null }[];
    message?: string;
  } | undefined;
  const geoPayload = explorer.data as { available?: boolean; items?: { id: string; employment_rate?: number | null }[]; message?: string } | undefined;
  const enumPayload = enumerators.data as {
    available?: boolean;
    items?: { id: string; employment_rate?: number | null }[];
    message?: string;
  } | undefined;

  const detectorItems = detectorPayload?.items ?? [];
  const temporalItems = temporalPayload?.items ?? [];
  const geoItems = (geoPayload?.items ?? []).map((item) => ({
    id: item.id,
    value: item.employment_rate ?? null,
  }));
  const comparison = (enumPayload?.items ?? []).map((item) => ({
    enumerator_id: String(item.id),
    employment_rate: item.employment_rate ?? null,
  }));

  return (
    <div className="space-y-6">
      <PageHeader batchId={batchId} />

      <section className="sv-card p-5">
        <h2 className="text-sm font-semibold text-inst-navy">Temporal trends</h2>
        {temporal.isError ? (
          <div className="mt-4">
            <ErrorState message="Temporal analytics could not be loaded." onRetry={() => temporal.refetch()} />
          </div>
        ) : temporal.isPending ? (
          <div className="mt-4">
            <ChartSkeleton />
          </div>
        ) : temporalItems.length ? (
          <div className="mt-4">
            <TemporalTrendChart items={temporalItems} />
          </div>
        ) : (
          <div className="mt-4 flex items-start gap-3 rounded border border-inst-border bg-inst-muted px-4 py-5">
            <Clock3 className="mt-0.5 h-5 w-5 shrink-0 text-inst-blue" aria-hidden="true" />
            <div>
              <p className="font-semibold text-inst-navy">No previous survey period available</p>
              <p className="mt-1 text-sm leading-6 text-inst-text-secondary">
                Historical comparison will appear when a comparable previous survey period is available.
              </p>
              {temporalPayload?.message &&
              !/no previous survey period/i.test(temporalPayload.message) ? (
                <p className="mt-2 text-xs text-inst-text-secondary">{temporalPayload.message}</p>
              ) : null}
            </div>
          </div>
        )}
      </section>

      <section className="sv-card p-5">
        <h2 className="text-sm font-semibold text-inst-navy">Anomalies by detector</h2>
        <p className="mt-1 text-sm text-inst-text-secondary">Detected quality signals grouped by detector.</p>
        {detectors.isError ? (
          <div className="mt-4">
            <ErrorState message="Detector analytics could not be loaded." onRetry={() => detectors.refetch()} />
          </div>
        ) : detectors.isPending ? (
          <div className="mt-4">
            <ChartSkeleton />
          </div>
        ) : detectorItems.length ? (
          <div className="mt-4">
            <DetectorDistributionChart items={detectorItems} />
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState title="No data available" detail={detectorPayload?.message || "There is not enough data in this batch to display this analysis."} />
          </div>
        )}
      </section>

      <section className="sv-card p-5">
        <h2 className="text-sm font-semibold text-inst-navy">District employment rates</h2>
        <p className="mt-1 text-sm text-inst-text-secondary">Employment rate distribution across districts in the selected batch.</p>
        {explorer.isError ? (
          <div className="mt-4">
            <ErrorState message="District analytics could not be loaded." onRetry={() => explorer.refetch()} />
          </div>
        ) : explorer.isPending ? (
          <div className="mt-4">
            <ChartSkeleton />
          </div>
        ) : geoItems.length ? (
          <div className="mt-4">
            <GeographicComparisonChart items={geoItems} />
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState title="No data available" detail={geoPayload?.message || "There is not enough data in this batch to display this analysis."} />
          </div>
        )}
      </section>

      <section className="sv-card p-5">
        <h2 className="text-sm font-semibold text-inst-navy">Enumerator comparison</h2>
        <p className="mt-1 text-sm text-inst-text-secondary">Employment rate comparison across enumerators in the selected batch.</p>
        {enumerators.isError ? (
          <div className="mt-4">
            <ErrorState message="Enumerator analytics could not be loaded." onRetry={() => enumerators.refetch()} />
          </div>
        ) : enumerators.isPending ? (
          <div className="mt-4">
            <ChartSkeleton />
          </div>
        ) : comparison.length ? (
          <div className="mt-4">
            <EnumeratorComparisonChart items={comparison} />
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState title="No data available" detail={enumPayload?.message || "There is not enough data in this batch to display this analysis."} />
          </div>
        )}
      </section>
    </div>
  );
}

function PageHeader({ batchId }: { batchId: string }) {
  return (
    <div>
      <p className="sv-label">Analytics</p>
      <h1 className="mt-1 text-2xl font-semibold text-inst-navy">Quality explorer</h1>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-inst-text-secondary">
        Explore statistical patterns, anomalies and quality signals across the selected survey batch.
      </p>
      <p className="mt-3 text-sm text-inst-text">
        Batch <span className="font-mono text-xs font-semibold text-inst-navy">{batchId}</span>
      </p>
    </div>
  );
}
