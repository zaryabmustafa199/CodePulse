"use client";

import { useState, useRef } from "react";
import { Send, FolderOpen } from "lucide-react";
import { EngineeringReport, AnalysisError } from "@/app/types";

interface HeroInputProps {
  onStart: () => void;
  onSuccess: (report: EngineeringReport) => void;
  onError: (msg: string) => void;
  loading: boolean;
}

const PLACEHOLDER = "D:\\Projects\\PORTFOLIO\\MyRepo";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function HeroInput({ onStart, onSuccess, onError, loading }: HeroInputProps) {
  const [path, setPath] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = path.trim();
    if (!trimmed) {
      inputRef.current?.focus();
      return;
    }

    onStart();

    try {
      const res = await fetch(`${API_BASE}/api/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repository_path: trimmed }),
      });

      if (!res.ok) {
        const err: AnalysisError = await res.json().catch(() => ({ detail: "Unknown error" }));
        onError(err.detail ?? `HTTP ${res.status}`);
        return;
      }

      const report: EngineeringReport = await res.json();
      onSuccess(report);
    } catch (err) {
      onError("Could not reach the CodePulse API. Is the backend running on port 8000?");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px", alignItems: "center", textAlign: "center" }}>

      {/* Wordmark */}
      <div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.75rem",
            letterSpacing: "0.25em",
            textTransform: "uppercase",
            color: "var(--accent)",
            marginBottom: "12px",
            fontWeight: 700,
          }}
        >
          CodePulse
        </div>
        <h1
          style={{
            fontSize: "clamp(2rem, 5vw, 3.25rem)",
            fontWeight: 800,
            color: "var(--text-primary)",
            lineHeight: 1.15,
            letterSpacing: "-0.02em",
            maxWidth: "680px",
          }}
        >
          Multi-Agent Codebase<br />
          <span style={{ color: "var(--accent)" }}>Intelligence Engine</span>
        </h1>
        <p
          style={{
            marginTop: "16px",
            color: "var(--text-muted)",
            fontSize: "1.05rem",
            maxWidth: "520px",
            lineHeight: 1.65,
          }}
        >
          Submit a local repository path. Six domain agents analyze architecture,
          security, quality, documentation, and dependencies in parallel.
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          gap: "8px",
          width: "100%",
          maxWidth: "680px",
          alignItems: "center",
        }}
      >
        <div style={{ position: "relative", flex: 1 }}>
          <FolderOpen
            size={16}
            style={{
              position: "absolute",
              left: "14px",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-subtle)",
              pointerEvents: "none",
            }}
          />
          <input
            ref={inputRef}
            id="repo-path-input"
            className="cp-input"
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder={PLACEHOLDER}
            disabled={loading}
            style={{ paddingLeft: "40px" }}
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <button
          id="analyze-submit-btn"
          type="submit"
          className="cp-btn-primary"
          disabled={loading || !path.trim()}
        >
          <Send size={14} />
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {/* Hint */}
      <p style={{ color: "var(--text-subtle)", fontSize: "0.8rem", fontFamily: "var(--font-mono)" }}>
        Paste an absolute local path to a Python or TypeScript/JavaScript repository
      </p>
    </div>
  );
}
