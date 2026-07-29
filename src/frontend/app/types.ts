// ============================================================
// CodePulse Frontend — Canonical TypeScript Types
// Derived directly from src/backend/models/schemas.py
// ============================================================

export type AgentDomain =
  | "overview"
  | "architecture"
  | "code_quality"
  | "security"
  | "documentation"
  | "dependency";

export type Confidence = "high" | "medium" | "low" | "none";
export type Severity = "high" | "medium" | "low";
export type Grade = "A" | "B" | "C" | "D" | "F" | "N/A";

export interface AgentFinding {
  domain: AgentDomain;
  score: number | null;
  score_rationale: string;
  summary: string;
  strengths: string[];
  risks: string[];
  recommendations: string[];
  confidence: Confidence;
  prompt_version: string;
}

export interface EngineeringReport {
  analysis_id: string | null;
  status: string;
  total_latency_seconds: number;
  overall_score: number | null;
  overall_grade: Grade;
  executive_summary: string;
  repository_path: string;
  primary_language: string;
  total_files: number;
  total_lines: number;
  domain_findings: Partial<Record<AgentDomain, AgentFinding>>;
  timestamp: string;
}

export interface AnalysisError {
  detail: string;
}
