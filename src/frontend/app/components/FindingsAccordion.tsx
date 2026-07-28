"use client";

import { useState } from "react";
import { AgentFinding, AgentDomain, DOMAIN_META } from "@/app/types";
import { ChevronDown, ShieldAlert, TrendingUp, Lightbulb } from "lucide-react";

interface FindingItemProps {
  text: string;
  type: "risk" | "strength" | "recommendation";
}

function FindingItem({ text, type }: FindingItemProps) {
  const styles = {
    risk:           { icon: <ShieldAlert size={13} />, color: "var(--danger)", bg: "var(--danger-dim)" },
    strength:       { icon: <TrendingUp  size={13} />, color: "var(--accent)",  bg: "var(--accent-dim)" },
    recommendation: { icon: <Lightbulb  size={13} />, color: "var(--warn)",   bg: "var(--warn-dim)" },
  };
  const s = styles[type];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "10px",
        padding: "8px 12px",
        borderRadius: "var(--radius-sm)",
        background: s.bg,
        color: "var(--text-primary)",
        fontSize: "0.83rem",
        lineHeight: 1.55,
      }}
    >
      <span style={{ color: s.color, marginTop: "2px", flexShrink: 0 }}>{s.icon}</span>
      <span>{text}</span>
    </div>
  );
}

interface DomainAccordionProps {
  domain: AgentDomain;
  finding: AgentFinding;
  defaultOpen?: boolean;
}

function DomainAccordion({ domain, finding, defaultOpen = false }: DomainAccordionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const meta = DOMAIN_META[domain];
  const score = finding.score;
  const scoreColor =
    score === null ? "var(--text-muted)"
    : score >= 9 ? "hsl(158,85%,52%)"
    : score >= 7 ? "hsl(200,85%,55%)"
    : score >= 5 ? "hsl(40,95%,60%)"
    : "hsl(4,90%,60%)";

  return (
    <div className="glass-card" style={{ overflow: "hidden" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          width: "100%",
          padding: "16px 20px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          gap: "16px",
          textAlign: "left",
        }}
      >
        {/* Score ring */}
        <div
          style={{
            width: "40px",
            height: "40px",
            borderRadius: "50%",
            border: `2px solid ${scoreColor}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "var(--font-mono)",
            fontWeight: 700,
            fontSize: "0.9rem",
            color: scoreColor,
            background: `${scoreColor}18`,
            flexShrink: 0,
          }}
        >
          {score ?? "—"}
        </div>

        {/* Label + summary preview */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "var(--text-muted)",
              marginBottom: "3px",
            }}
          >
            {meta.label}
          </div>
          <div
            style={{
              color: "var(--text-primary)",
              fontSize: "0.88rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: open ? "normal" : "nowrap",
              lineHeight: 1.4,
            }}
          >
            {finding.summary}
          </div>
        </div>

        {/* Chevron */}
        <ChevronDown
          size={18}
          style={{
            color: "var(--text-muted)",
            flexShrink: 0,
            transition: "transform 0.2s ease",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
          }}
        />
      </button>

      {/* Expanded content */}
      {open && (
        <div
          style={{
            borderTop: "1px solid var(--border)",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {finding.strengths.length > 0 && (
            <div>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--accent)", fontFamily: "var(--font-mono)", marginBottom: "8px" }}>
                Strengths
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {finding.strengths.map((s, i) => <FindingItem key={i} text={s} type="strength" />)}
              </div>
            </div>
          )}

          {finding.risks.length > 0 && (
            <div>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--danger)", fontFamily: "var(--font-mono)", marginBottom: "8px" }}>
                Risks
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {finding.risks.map((r, i) => <FindingItem key={i} text={r} type="risk" />)}
              </div>
            </div>
          )}

          {finding.recommendations.length > 0 && (
            <div>
              <div style={{ fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--warn)", fontFamily: "var(--font-mono)", marginBottom: "8px" }}>
                Recommendations
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {finding.recommendations.map((r, i) => <FindingItem key={i} text={r} type="recommendation" />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface FindingsAccordionProps {
  report: import("@/app/types").EngineeringReport;
}

export default function FindingsAccordion({ report }: FindingsAccordionProps) {
  const entries = Object.entries(report.domain_findings) as [AgentDomain, AgentFinding][];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      {entries.map(([domain, finding], i) => (
        <DomainAccordion
          key={domain}
          domain={domain}
          finding={finding}
          defaultOpen={i === 0}
        />
      ))}
    </div>
  );
}
