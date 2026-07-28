"use client";

import {
  RadarChart as RechartsRadar,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { EngineeringReport, DOMAIN_META, DOMAIN_ORDER } from "@/app/types";

interface RadarChartProps {
  report: EngineeringReport;
}

interface RadarDatum {
  domain: string;
  score: number;
  fullMark: number;
}

// Exact transform from implementation_plan.md
function toRadarData(report: EngineeringReport): RadarDatum[] {
  return DOMAIN_ORDER.map((key) => {
    const finding = report.domain_findings[key];
    return {
      domain: DOMAIN_META[key].shortLabel,
      score:  finding?.score ?? 0,
      fullMark: 10,
    };
  });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          background: "var(--bg-base)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-sm)",
          padding: "8px 14px",
          fontFamily: "var(--font-mono)",
          fontSize: "0.8rem",
          color: "var(--text-primary)",
        }}
      >
        <div style={{ color: "var(--accent)", fontWeight: 700 }}>
          {payload[0]?.payload?.domain}
        </div>
        <div style={{ color: "var(--text-muted)" }}>
          Score: <span style={{ color: "var(--text-primary)" }}>{payload[0]?.value ?? 0}</span> / 10
        </div>
      </div>
    );
  }
  return null;
};

export default function RadarChart({ report }: RadarChartProps) {
  const data = toRadarData(report);

  return (
    <div
      className="glass-card"
      style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "12px" }}
    >
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.72rem",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
          fontWeight: 700,
        }}
      >
        Domain Score Radar
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <RechartsRadar data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid
            stroke="rgba(255,255,255,0.07)"
            gridType="polygon"
          />
          <PolarAngleAxis
            dataKey="domain"
            tick={{
              fill: "var(--text-muted)",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
            }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="hsl(158,85%,52%)"
            fill="hsl(158,85%,52%)"
            fillOpacity={0.18}
            strokeWidth={2}
            dot={{ fill: "hsl(158,85%,52%)", r: 4, strokeWidth: 0 }}
          />
          <Tooltip content={<CustomTooltip />} />
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}
