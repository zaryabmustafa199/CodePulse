"use client";

import { useState, useEffect } from "react";
import { Sun, Moon, ArrowRight } from "lucide-react";
import { EngineeringReport, AgentFinding } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/* ------------------------------------------------------------------ */
/*  Grade badge color helper                                          */
/* ------------------------------------------------------------------ */
function gradeColor(g: string) {
  switch (g) {
    case "A": return "var(--green)";
    case "B": return "var(--blue)";
    case "C": return "var(--amber)";
    case "D": return "var(--amber)";
    default:  return "var(--red)";
  }
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */
export default function Home() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [repoPath, setRepoPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<EngineeringReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = repoPath.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repository_path: trimmed }),
      });

      if (!res.ok) {
        let msg = `Server returned ${res.status}`;
        try { const d = await res.json(); msg = d.detail || msg; } catch {}
        setError(msg);
        return;
      }

      const data: EngineeringReport = await res.json();
      if (data.status === "error") {
        setError(data.executive_summary || "Analysis failed.");
      } else {
        setReport(data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      setError(`${msg}. Make sure the backend is running on port 8000.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* ─── Header ─── */}
      <header
        style={{
          padding: "0 clamp(1.5rem, 4vw, 3rem)",
          height: "56px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <a
          href="/"
          style={{
            fontSize: "1.05rem",
            fontWeight: 700,
            color: "var(--text)",
            textDecoration: "none",
            letterSpacing: "-0.02em",
          }}
        >
          CodePulse
        </a>

        <button
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          aria-label="Toggle theme"
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            border: "1px solid var(--border)",
            background: "var(--bg-raised)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-secondary)",
            transition: "all var(--transition)",
          }}
        >
          {theme === "light" ? <Moon size={15} /> : <Sun size={15} />}
        </button>
      </header>

      {/* ─── Pulse line ─── */}
      <div className="pulse-line" />

      {/* ─── Main ─── */}
      <main style={{ flex: 1, width: "100%", maxWidth: "640px", margin: "0 auto", padding: "0 1.5rem" }}>

        {/* Hero */}
        <section style={{ paddingTop: "clamp(3rem, 8vh, 6rem)", paddingBottom: "2rem" }}>
          <h1
            style={{
              fontSize: "clamp(2rem, 4.5vw, 3rem)",
              fontWeight: 800,
              letterSpacing: "-0.035em",
              lineHeight: 1.1,
              color: "var(--text)",
            }}
          >
            Analyze any codebase.
          </h1>
          <p
            style={{
              marginTop: "0.75rem",
              fontSize: "1.05rem",
              color: "var(--text-secondary)",
              lineHeight: 1.55,
              maxWidth: "520px",
            }}
          >
            Paste a GitHub URL or local path. Six AI agents audit your architecture,
            security, code quality, docs, and dependencies — in seconds.
          </p>
        </section>

        {/* Input */}
        <form onSubmit={handleAnalyze} style={{ display: "flex", gap: "8px" }}>
          <input
            type="text"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="https://github.com/owner/repo"
            disabled={loading}
            style={{
              flex: 1,
              height: "48px",
              padding: "0 16px",
              fontSize: "0.925rem",
              fontFamily: "var(--font-mono)",
              color: "var(--text)",
              background: "var(--bg-raised)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              outline: "none",
              transition: "border var(--transition), box-shadow var(--transition)",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--border-focus)";
              e.currentTarget.style.boxShadow = "0 0 0 3px var(--accent-soft)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
          <button
            type="submit"
            disabled={loading || !repoPath.trim()}
            style={{
              height: "48px",
              padding: "0 20px",
              fontSize: "0.875rem",
              fontWeight: 600,
              color: "var(--bg)",
              background: "var(--accent)",
              border: "none",
              borderRadius: "var(--radius-sm)",
              cursor: loading || !repoPath.trim() ? "not-allowed" : "pointer",
              opacity: loading || !repoPath.trim() ? 0.5 : 1,
              display: "flex",
              alignItems: "center",
              gap: "6px",
              whiteSpace: "nowrap",
              transition: "opacity var(--transition)",
            }}
          >
            {loading ? "Analyzing…" : "Analyze"} <ArrowRight size={16} />
          </button>
        </form>

        {/* Error */}
        {error && (
          <div
            style={{
              marginTop: "1.25rem",
              padding: "12px 16px",
              fontSize: "0.875rem",
              color: "var(--red)",
              background: "var(--red-bg)",
              border: "1px solid var(--red-border)",
              borderRadius: "var(--radius-sm)",
              lineHeight: 1.5,
            }}
          >
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ marginTop: "2rem", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              <span className="pulse-line-short" />
              Running analysis pipeline…
            </div>
            <div className="skeleton" style={{ height: "100px" }} />
            <div className="skeleton" style={{ height: "60px" }} />
            <div className="skeleton" style={{ height: "200px" }} />
          </div>
        )}

        {/* ─── Results ─── */}
        {report && !loading && (
          <div style={{ marginTop: "2.5rem", display: "flex", flexDirection: "column", gap: "2rem", paddingBottom: "3rem" }}>

            {/* Overall Score Card */}
            <div
              style={{
                padding: "1.5rem",
                background: "var(--bg-raised)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
                boxShadow: "var(--shadow-sm)",
                display: "flex",
                gap: "1.5rem",
                alignItems: "flex-start",
              }}
            >
              {/* Grade */}
              <div style={{ textAlign: "center", flexShrink: 0 }}>
                <div
                  style={{
                    width: "64px",
                    height: "64px",
                    borderRadius: "16px",
                    border: `2px solid ${gradeColor(report.overall_grade)}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span style={{ fontSize: "2rem", fontWeight: 800, color: gradeColor(report.overall_grade), fontFamily: "var(--font-mono)" }}>
                    {report.overall_grade}
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                  {report.overall_score}/10
                </div>
              </div>

              {/* Summary */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: "0.925rem", color: "var(--text)", lineHeight: 1.6 }}>
                  {report.executive_summary}
                </p>
                <div style={{ marginTop: "10px", display: "flex", gap: "16px", flexWrap: "wrap", fontSize: "0.8rem", fontFamily: "var(--font-mono)", color: "var(--text-tertiary)" }}>
                  <span>{report.total_files} files</span>
                  <span>{report.total_lines.toLocaleString()} lines</span>
                  <span>{report.primary_language}</span>
                  <span>{report.total_latency_seconds.toFixed(1)}s</span>
                </div>
              </div>
            </div>

            {/* Domain Scores Row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "8px" }}>
              {Object.entries(report.domain_findings)
                .filter(([k]) => k !== "overview")
                .map(([key, finding]) => {
                  const f = finding as AgentFinding;
                  const score = f.score ?? 0;
                  return (
                    <div
                      key={key}
                      style={{
                        padding: "14px 16px",
                        background: "var(--bg-raised)",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                        textAlign: "center",
                      }}
                    >
                      <div style={{ fontSize: "1.5rem", fontWeight: 800, fontFamily: "var(--font-mono)", color: score >= 8 ? "var(--green)" : score >= 6 ? "var(--amber)" : "var(--red)" }}>
                        {score}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", textTransform: "capitalize", marginTop: "2px" }}>
                        {key.replace("_", " ")}
                      </div>
                    </div>
                  );
                })}
            </div>

            {/* Findings */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {Object.entries(report.domain_findings)
                .filter(([k]) => k !== "overview")
                .map(([key, finding]) => {
                  const f = finding as AgentFinding;
                  return <FindingSection key={key} domain={key} finding={f} />;
                })}
            </div>
          </div>
        )}
      </main>

      {/* ─── Footer ─── */}
      <footer
        style={{
          borderTop: "1px solid var(--border)",
          padding: "2rem clamp(1.5rem, 4vw, 3rem)",
          marginTop: "auto",
        }}
      >
        <div style={{ maxWidth: "640px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text)" }}>CodePulse</span>
            <nav style={{ display: "flex", gap: "1.25rem", fontSize: "0.825rem" }}>
              <a href="#privacy" style={{ color: "var(--text-tertiary)", textDecoration: "none" }}>Privacy</a>
              <a href="#terms" style={{ color: "var(--text-tertiary)", textDecoration: "none" }}>Terms</a>
              <a href="#contact" style={{ color: "var(--text-tertiary)", textDecoration: "none" }}>Contact</a>
            </nav>
          </div>
          <div style={{ fontSize: "0.775rem", color: "var(--text-tertiary)" }}>
            © 2026 CodePulse. Multi-agent code intelligence powered by Tree-sitter AST analysis and Gemini.
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Finding Section (collapsible per domain)                           */
/* ------------------------------------------------------------------ */
function FindingSection({ domain, finding }: { domain: string; finding: AgentFinding }) {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        background: "var(--bg-raised)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%",
          padding: "14px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "var(--text)",
          fontSize: "0.9rem",
          fontWeight: 600,
          textTransform: "capitalize",
        }}
      >
        <span>{domain.replace("_", " ")}</span>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "0.8rem", fontFamily: "var(--font-mono)", color: "var(--text-tertiary)", fontWeight: 400 }}>
            {finding.score}/10
          </span>
          <span style={{ fontSize: "0.8rem", color: "var(--text-tertiary)", transform: open ? "rotate(180deg)" : "none", transition: "transform var(--transition)" }}>
            ▾
          </span>
        </div>
      </button>

      {open && (
        <div style={{ padding: "0 16px 16px", display: "flex", flexDirection: "column", gap: "14px" }}>
          {/* Summary */}
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6, borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
            {finding.summary}
          </p>

          {/* Strengths */}
          {finding.strengths.length > 0 && (
            <div>
              <h4 style={{ fontSize: "0.75rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--green)", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Strengths
              </h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "4px" }}>
                {finding.strengths.map((s, i) => (
                  <li
                    key={i}
                    style={{
                      fontSize: "0.85rem",
                      color: "var(--text)",
                      padding: "8px 12px",
                      background: "var(--green-bg)",
                      border: "1px solid var(--green-border)",
                      borderRadius: "var(--radius-xs)",
                      lineHeight: 1.5,
                    }}
                  >
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risks */}
          {finding.risks.length > 0 && (
            <div>
              <h4 style={{ fontSize: "0.75rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--red)", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Risks
              </h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "4px" }}>
                {finding.risks.map((r, i) => (
                  <li
                    key={i}
                    style={{
                      fontSize: "0.85rem",
                      color: "var(--text)",
                      padding: "8px 12px",
                      background: "var(--red-bg)",
                      border: "1px solid var(--red-border)",
                      borderRadius: "var(--radius-xs)",
                      lineHeight: 1.5,
                    }}
                  >
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {finding.recommendations.length > 0 && (
            <div>
              <h4 style={{ fontSize: "0.75rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--amber)", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Recommendations
              </h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "4px" }}>
                {finding.recommendations.map((r, i) => (
                  <li
                    key={i}
                    style={{
                      fontSize: "0.85rem",
                      color: "var(--text)",
                      padding: "8px 12px",
                      background: "var(--amber-bg)",
                      border: "1px solid var(--amber-border)",
                      borderRadius: "var(--radius-xs)",
                      lineHeight: 1.5,
                    }}
                  >
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
