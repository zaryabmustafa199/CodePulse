"use client";

import { useState } from "react";
import { EngineeringReport, Grade } from "@/app/types";
import HeroInput from "@/app/components/HeroInput";
import AnalysisState from "@/app/components/AnalysisState";
import OverallScore from "@/app/components/OverallScore";
import MetaBar from "@/app/components/MetaBar";
import RadarChart from "@/app/components/RadarChart";
import DomainGrid from "@/app/components/DomainGrid";
import FindingsAccordion from "@/app/components/FindingsAccordion";
import ExportButton from "@/app/components/ExportButton";
import { AlertCircle, RefreshCw } from "lucide-react";

type AppState = "idle" | "loading" | "success" | "error";

export default function HomePage() {
  const [appState, setAppState]   = useState<AppState>("idle");
  const [report,   setReport]     = useState<EngineeringReport | null>(null);
  const [errorMsg, setErrorMsg]   = useState<string>("");

  const handleStart = () => {
    setAppState("loading");
    setErrorMsg("");
    setReport(null);
  };

  const handleSuccess = (r: EngineeringReport) => {
    setReport(r);
    setAppState("success");
  };

  const handleError = (msg: string) => {
    setErrorMsg(msg);
    setAppState("error");
  };

  const handleReset = () => {
    setAppState("idle");
    setReport(null);
    setErrorMsg("");
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "clamp(40px, 6vw, 80px) clamp(16px, 5vw, 48px)",
        gap: "48px",
        maxWidth: "1200px",
        margin: "0 auto",
        width: "100%",
      }}
    >
      {/* Hero always visible */}
      <HeroInput
        onStart={handleStart}
        onSuccess={handleSuccess}
        onError={handleError}
        loading={appState === "loading"}
      />

      {/* Loading skeleton */}
      {appState === "loading" && <AnalysisState />}

      {/* Error state */}
      {appState === "error" && (
        <div
          className="glass-card"
          style={{
            width: "100%",
            padding: "24px 32px",
            display: "flex",
            alignItems: "center",
            gap: "16px",
            borderColor: "hsla(4,90%,60%,0.3)",
          }}
        >
          <AlertCircle size={20} style={{ color: "var(--danger)", flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                fontWeight: 700,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "var(--danger)",
                marginBottom: "4px",
              }}
            >
              Analysis Failed
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>{errorMsg}</p>
          </div>
          <button className="cp-btn-ghost" onClick={handleReset}>
            <RefreshCw size={13} />
            Try Again
          </button>
        </div>
      )}

      {/* Report */}
      {appState === "success" && report && (
        <div
          style={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            gap: "24px",
            animation: "fadeIn 0.4s ease",
          }}
        >
          {/* Section header + actions */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                fontWeight: 700,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: "var(--text-muted)",
              }}
            >
              Engineering Report
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <ExportButton report={report} />
              <button className="cp-btn-ghost" onClick={handleReset}>
                <RefreshCw size={13} />
                New Analysis
              </button>
            </div>
          </div>

          {/* Overall grade */}
          <OverallScore
            score={report.overall_score}
            grade={report.overall_grade as Grade}
            summary={report.executive_summary}
          />

          {/* Meta bar */}
          <MetaBar report={report} />

          {/* Radar + domain grid side by side on wide screens */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(280px, 380px) 1fr",
              gap: "24px",
              alignItems: "start",
            }}
          >
            <RadarChart report={report} />
            <DomainGrid report={report} />
          </div>

          {/* Accordion section header */}
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.72rem",
              fontWeight: 700,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: "var(--text-muted)",
              paddingTop: "8px",
              borderTop: "1px solid var(--border)",
            }}
          >
            Domain Findings
          </div>

          {/* Findings accordion */}
          <FindingsAccordion report={report} />

          {/* Footer */}
          <div
            style={{
              marginTop: "16px",
              paddingTop: "16px",
              borderTop: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                color: "var(--text-subtle)",
              }}
            >
              {report.analysis_id ? `ID: ${report.analysis_id.slice(0, 8)}…` : ""}
            </span>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                color: "var(--text-subtle)",
              }}
            >
              {new Date(report.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </main>
  );
}

// Fade-in animation added inline via style injection
// (avoids needing additional keyframe import)
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = `@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }`;
  document.head.appendChild(style);
}
