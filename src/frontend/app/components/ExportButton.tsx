"use client";

import { Download } from "lucide-react";
import { EngineeringReport } from "@/app/types";

interface ExportButtonProps {
  report: EngineeringReport;
}

export default function ExportButton({ report }: ExportButtonProps) {
  const handleExport = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const name = report.repository_path.split(/[\\/]/).pop() ?? "report";
    const ts   = new Date().toISOString().slice(0, 10);
    link.href     = url;
    link.download = `codepulse-${name}-${ts}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      className="cp-btn-ghost"
      onClick={handleExport}
      title="Download full report as JSON"
    >
      <Download size={14} />
      Export JSON
    </button>
  );
}
