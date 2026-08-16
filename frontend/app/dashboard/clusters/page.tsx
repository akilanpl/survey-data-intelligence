"use client";

import { ClusterTable } from "@/components/group-tables";

export default function ClustersPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="sv-label">Clusters</p>
        <h1 className="mt-1 text-2xl font-semibold text-inst-navy">Geographic grouping</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-inst-text-secondary">
          Monitor workload, anomaly concentration, and data-quality signals across geographic clusters.
        </p>
      </div>
      <ClusterTable />
    </div>
  );
}
