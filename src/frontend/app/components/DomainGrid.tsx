"use client";

import { EngineeringReport, DOMAIN_ORDER } from "@/app/types";
import DomainCard from "./DomainCard";

interface DomainGridProps {
  report: EngineeringReport;
}

export default function DomainGrid({ report }: DomainGridProps) {
  const entries = DOMAIN_ORDER.filter((d) => d !== "overview" && report.domain_findings[d]);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
        gap: "16px",
      }}
    >
      {entries.map((domain) => {
        const finding = report.domain_findings[domain];
        if (!finding) return null;
        return <DomainCard key={domain} domain={domain} finding={finding} />;
      })}
    </div>
  );
}
