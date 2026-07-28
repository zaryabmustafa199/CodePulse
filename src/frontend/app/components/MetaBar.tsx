"use client";

import { EngineeringReport } from "@/app/types";
import { Clock, FileText, Code2, Cpu } from "lucide-react";

interface MetaBarProps {
  report: EngineeringReport;
}

const LANG_COLORS: Record<string, string> = {
  python:     "hsl(205,85%,60%)",
  typescript: "hsl(210,100%,65%)",
  javascript: "hsl(48,95%,55%)",
  unknown:    "var(--text-muted)",
};

export default function MetaBar({ report }: MetaBarProps) {
  const langColor = LANG_COLORS[report.primary_language.toLowerCase()] ?? "var(--text-muted)";

  const items = [
    {
      icon: <Clock size={14} />,
      label: "Latency",
      value: `${report.total_latency_seconds.toFixed(2)}s`,
    },
    {
      icon: <FileText size={14} />,
      label: "Files",
      value: report.total_files.toLocaleString(),
    },
    {
      icon: <Code2 size={14} />,
      label: "Lines",
      value: report.total_lines.toLocaleString(),
    },
    {
      icon: <Cpu size={14} />,
      label: "Language",
      value: report.primary_language.charAt(0).toUpperCase() + report.primary_language.slice(1),
      color: langColor,
    },
  ];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "4px",
        flexWrap: "wrap",
      }}
    >
      {items.map((item, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>{item.icon}</span>
            <span style={{ color: "var(--text-muted)" }}>{item.label}</span>
            <span style={{ color: item.color ?? "var(--text-primary)", fontWeight: 600 }}>
              {item.value}
            </span>
          </div>
          {i < items.length - 1 && (
            <span style={{ color: "var(--border)", padding: "0 2px" }}>·</span>
          )}
        </div>
      ))}

      {/* Repo path */}
      <div
        style={{
          marginLeft: "auto",
          padding: "6px 14px",
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-sm)",
          fontFamily: "var(--font-mono)",
          fontSize: "0.75rem",
          color: "var(--text-subtle)",
          maxWidth: "320px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
        title={report.repository_path}
      >
        {report.repository_path}
      </div>
    </div>
  );
}
