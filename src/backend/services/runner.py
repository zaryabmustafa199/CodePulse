"""
Analysis Runner Service for CodePulse.
Executes static analysis tools (Ruff) via subprocess, parses JSON diagnostics,
and packages RepositoryContext and ParsedRepository into an AnalysisBundle.
"""

import json
import subprocess
from pathlib import Path
from typing import List
from src.backend.models.schemas import RepositoryContext, ParsedRepository, AnalysisBundle, StaticFinding


class AnalysisRunnerService:
    """Service to execute static tools (Ruff) and construct AnalysisBundle."""

    @staticmethod
    def run_ruff(repo_path_str: str) -> List[StaticFinding]:
        """Run Ruff static linter and return parsed StaticFinding instances."""
        findings: List[StaticFinding] = []
        repo_path = Path(repo_path_str).resolve()

        try:
            # Run ruff check with json output format
            cmd = ["ruff", "check", str(repo_path), "--output-format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.stdout:
                raw_json = json.loads(result.stdout)
                for item in raw_json:
                    filename = item.get("filename", "")
                    try:
                        rel_path = Path(filename).relative_to(repo_path).as_posix()
                    except Exception:
                        rel_path = filename

                    findings.append(StaticFinding(
                        tool_name="ruff",
                        rule_id=item.get("code", "E999"),
                        message=item.get("message", ""),
                        file_path=rel_path,
                        line_number=item.get("location", {}).get("row", 1),
                        severity="medium",
                        category="code_quality"
                    ))
        except Exception:
            pass  # Fallback to empty findings if ruff is unavailable or times out

        return findings

    @classmethod
    def create_bundle(cls, context: RepositoryContext, parsed: ParsedRepository) -> AnalysisBundle:
        """Execute static tool passes and construct AnalysisBundle."""
        ruff_findings = cls.run_ruff(context.repository_path)
        tool_status = {"ruff": "success" if ruff_findings else "no_findings_or_skipped"}

        return AnalysisBundle(
            context=context,
            parsed_repo=parsed,
            static_findings=ruff_findings,
            tool_status=tool_status
        )
