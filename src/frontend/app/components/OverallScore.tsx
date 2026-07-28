"use client";

import { Grade } from "@/app/types";

const GRADE_STYLES: Record<Grade, { color: string; glow: string; label: string }> = {
  A:   { color: "hsl(158,85%,52%)", glow: "hsla(158,85%,52%,0.3)",  label: "Excellent" },
  B:   { color: "hsl(200,85%,55%)", glow: "hsla(200,85%,55%,0.3)",  label: "Good" },
  C:   { color: "hsl(40,95%,60%)",  glow: "hsla(40,95%,60%,0.3)",   label: "Fair" },
  D:   { color: "hsl(20,90%,58%)",  glow: "hsla(20,90%,58%,0.3)",   label: "Poor" },
  F:   { color: "hsl(4,90%,60%)",   glow: "hsla(4,90%,60%,0.3)",    label: "Critical" },
  "N/A": { color: "var(--text-muted)", glow: "transparent",          label: "N/A" },
};

interface OverallScoreProps {
  score: number | null;
  grade: Grade;
  summary: string;
}

export default function OverallScore({ score, grade, summary }: OverallScoreProps) {
  const style = GRADE_STYLES[grade] ?? GRADE_STYLES["N/A"];

  return (
    <div
      className="glass-card"
      style={{
        padding: "32px 40px",
        display: "flex",
        alignItems: "center",
        gap: "32px",
        borderColor: `hsla(${grade === "A" ? "158,85%,52%" : grade === "B" ? "200,85%,55%" : grade === "C" ? "40,95%,60%" : grade === "D" ? "20,90%,58%" : "4,90%,60%"},0.3)`,
      }}
    >
      {/* Giant grade letter */}
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "5rem",
          fontWeight: 800,
          lineHeight: 1,
          color: style.color,
          textShadow: `0 0 40px ${style.glow}`,
          minWidth: "80px",
          textAlign: "center",
        }}
      >
        {grade}
      </div>

      {/* Divider */}
      <div style={{ width: "1px", height: "80px", background: "var(--border)", flexShrink: 0 }} />

      {/* Score + label + summary */}
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "8px" }}>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "2.25rem",
              fontWeight: 700,
              color: style.color,
            }}
          >
            {score ?? "—"}
          </span>
          <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: "1rem" }}>
            / 10
          </span>
          <span
            style={{
              marginLeft: "8px",
              padding: "2px 10px",
              borderRadius: "999px",
              fontSize: "0.72rem",
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              fontFamily: "var(--font-mono)",
              background: `hsla(${grade === "A" ? "158,85%,52%,0.1" : grade === "B" ? "200,85%,55%,0.1" : grade === "C" ? "40,95%,60%,0.1" : grade === "D" ? "20,90%,58%,0.1" : "4,90%,60%,0.1"})`,
              color: style.color,
              border: `1px solid ${style.color}`,
            }}
          >
            {style.label}
          </span>
        </div>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: "0.9rem",
            lineHeight: 1.6,
            maxWidth: "600px",
          }}
        >
          {summary}
        </p>
      </div>
    </div>
  );
}
