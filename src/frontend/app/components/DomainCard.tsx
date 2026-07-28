"use client";

import { AgentFinding, AgentDomain, DOMAIN_META } from "@/app/types";

interface DomainCardProps {
  domain: AgentDomain;
  finding: AgentFinding;
}

const SCORE_COLOR = (score: number | null): string => {
  if (score === null) return "var(--text-muted)";
  if (score >= 9)  return "hsl(158,85%,52%)";
  if (score >= 7)  return "hsl(200,85%,55%)";
  if (score >= 5)  return "hsl(40,95%,60%)";
  return "hsl(4,90%,60%)";
};

const CONFIDENCE_STYLES: Record<string, { bg: string; color: string }> = {
  high:   { bg: "hsla(158,85%,52%,0.1)", color: "hsl(158,85%,52%)" },
  medium: { bg: "hsla(40,95%,60%,0.1)",  color: "hsl(40,95%,60%)" },
  low:    { bg: "hsla(4,90%,60%,0.1)",   color: "hsl(4,90%,60%)" },
  none:   { bg: "var(--bg-surface-2)",   color: "var(--text-muted)" },
};

export default function DomainCard({ domain, finding }: DomainCardProps) {
  const scoreColor = SCORE_COLOR(finding.score);
  const confStyle  = CONFIDENCE_STYLES[finding.confidence] ?? CONFIDENCE_STYLES.none;
  const meta       = DOMAIN_META[domain];

  return (
    <div
      className="glass-card"
      style={{
        padding: "20px 24px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        height: "100%",
        borderLeft: `3px solid ${scoreColor}`,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.75rem",
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
          }}
        >
          {meta.label}
        </span>
        <span
          style={{
            padding: "2px 8px",
            borderRadius: "999px",
            fontSize: "0.68rem",
            fontWeight: 600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            fontFamily: "var(--font-mono)",
            background: confStyle.bg,
            color: confStyle.color,
          }}
        >
          {finding.confidence}
        </span>
      </div>

      {/* Score */}
      <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "2.5rem",
            fontWeight: 800,
            color: scoreColor,
            lineHeight: 1,
          }}
        >
          {finding.score ?? "—"}
        </span>
        <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-subtle)", fontSize: "0.9rem" }}>
          /10
        </span>
      </div>

      {/* Rationale */}
      <p
        style={{
          color: "var(--text-muted)",
          fontSize: "0.82rem",
          lineHeight: 1.55,
          flexGrow: 1,
        }}
      >
        {finding.score_rationale}
      </p>
    </div>
  );
}
