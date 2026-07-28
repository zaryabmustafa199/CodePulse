"use client";

export default function AnalysisState() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      {/* Status text */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          fontFamily: "var(--font-mono)",
          fontSize: "0.9rem",
          color: "var(--text-muted)",
        }}
      >
        <span
          style={{
            display: "inline-block",
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "var(--accent)",
            animation: "pulse-skeleton 1s ease-in-out infinite",
          }}
        />
        Running 6-agent analysis pipeline…
      </div>

      {/* Skeleton: overall score card */}
      <div
        className="glass-card skeleton"
        style={{ height: "120px", borderRadius: "var(--radius-lg)" }}
      />

      {/* Skeleton: meta bar */}
      <div className="skeleton" style={{ height: "36px", borderRadius: "var(--radius-sm)", width: "60%" }} />

      {/* Skeleton: two-column layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div className="glass-card skeleton" style={{ height: "300px", borderRadius: "var(--radius-lg)" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="skeleton"
              style={{ height: "42px", borderRadius: "var(--radius-sm)", opacity: 1 - i * 0.12 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
