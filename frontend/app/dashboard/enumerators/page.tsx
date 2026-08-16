"use client";

import { EnumeratorTable } from "@/components/group-tables";

export default function EnumeratorsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="sv-label">Enumerators</p>
        <h1 className="mt-1 text-2xl font-semibold text-inst-navy">Workload and risk</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-inst-text-secondary">
          Monitor enumerator workload, anomaly signals, and data-quality risk across districts.
        </p>
      </div>
      <EnumeratorTable />
    </div>
  );
}
