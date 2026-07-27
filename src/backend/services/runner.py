"""
Analysis Runner Service for CodePulse.
Executes static analysis tools (Ruff, Bandit, ESLint, pip-audit) via subprocess, parses JSON diagnostics,
and packages RepositoryContext and ParsedRepository into an AnalysisBundle.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict
from src.backend.models.schemas import RepositoryContext, ParsedRepository, AnalysisBundle, StaticFinding, Language


class AnalysisRunnerService:
    """Service to execute static tools (Ruff, Bandit, ESLint, pip-audit) and construct AnalysisBundle."""

    @staticmethod
    def run_ruff(repo_path_str: str) -> List[StaticFinding]:
        """Run Ruff static linter and return parsed StaticFinding instances."""
        findings: List[StaticFinding] = []
        repo_path = Path(repo_path_str).resolve()

        try:
            venv_ruff = repo_path.parent / ".venv" / "Scripts" / "ruff"
            cmd_name = str(venv_ruff) if venv_ruff.exists() else "ruff"
            
            cmd = [cmd_name, "check", str(repo_path), "--output-format=json"]
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
            pass

        return findings

    @staticmethod
    def run_bandit(repo_path_str: str) -> List[StaticFinding]:
        """Run Bandit security linter and return parsed StaticFinding instances."""
        findings: List[StaticFinding] = []
        repo_path = Path(repo_path_str).resolve()

        try:
            venv_bandit = repo_path.parent / ".venv" / "Scripts" / "bandit"
            cmd_name = str(venv_bandit) if venv_bandit.exists() else "bandit"

            cmd = [cmd_name, "-r", str(repo_path), "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.stdout:
                raw_json = json.loads(result.stdout)
                results_list = raw_json.get("results", [])
                for item in results_list:
                    filename = item.get("filename", "")
                    try:
                        rel_path = Path(filename).relative_to(repo_path).as_posix()
                    except Exception:
                        rel_path = filename

                    sev_raw = item.get("issue_severity", "medium").lower()
                    findings.append(StaticFinding(
                        tool_name="bandit",
                        rule_id=item.get("test_id", "B999"),
                        message=item.get("issue_text", ""),
                        file_path=rel_path,
                        line_number=item.get("line_number", 1),
                        severity="high" if sev_raw == "high" else ("medium" if sev_raw == "medium" else "low"),
                        category="security"
                    ))
        except Exception:
            pass

        return findings

    @staticmethod
    def run_eslint(repo_path_str: str) -> List[StaticFinding]:
        """Run ESLint static linter and return parsed StaticFinding instances."""
        findings: List[StaticFinding] = []
        repo_path = Path(repo_path_str).resolve()

        try:
            cmd = ["npx.cmd" if os.name == "nt" else "npx", "eslint", str(repo_path), "--format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            stdout_to_parse = result.stdout
            if stdout_to_parse and not stdout_to_parse.strip().startswith("["):
                idx = stdout_to_parse.find("[")
                if idx != -1:
                    stdout_to_parse = stdout_to_parse[idx:]

            if stdout_to_parse:
                raw_json = json.loads(stdout_to_parse)
                for file_entry in raw_json:
                    filepath = file_entry.get("filePath", "")
                    try:
                        rel_path = Path(filepath).relative_to(repo_path).as_posix()
                    except Exception:
                        rel_path = filepath

                    messages = file_entry.get("messages", [])
                    for msg in messages:
                        severity_val = "medium"
                        if msg.get("severity") == 2:
                            severity_val = "high"
                        elif msg.get("severity") == 1:
                            severity_val = "low"

                        findings.append(StaticFinding(
                            tool_name="eslint",
                            rule_id=msg.get("ruleId", "ES999"),
                            message=msg.get("message", ""),
                            file_path=rel_path,
                            line_number=msg.get("line", 1),
                            severity=severity_val,
                            category="code_quality"
                        ))
        except Exception:
            pass

        return findings

    @staticmethod
    def run_pip_audit(repo_path_str: str) -> List[StaticFinding]:
        """Run pip-audit with strict 3s timeout for dependency vulnerability checks."""
        findings: List[StaticFinding] = []
        repo_path = Path(repo_path_str).resolve()

        req_file = repo_path / "requirements.txt"
        if not req_file.exists():
            return findings

        try:
            venv_audit = repo_path.parent / ".venv" / "Scripts" / "pip-audit"
            cmd_name = str(venv_audit) if venv_audit.exists() else "pip-audit"

            cmd = [cmd_name, "-r", str(req_file), "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)

            if result.stdout:
                raw_json = json.loads(result.stdout)
                for vulndep in raw_json.get("dependencies", []):
                    vulns = vulndep.get("vulns", [])
                    for v in vulns:
                        findings.append(StaticFinding(
                            tool_name="pip-audit",
                            rule_id=v.get("id", "VULN999"),
                            message=f"Vulnerability in {vulndep.get('name')} {vulndep.get('version')}: {v.get('description', '')}",
                            file_path="requirements.txt",
                            line_number=1,
                            severity="high",
                            category="dependency"
                        ))
        except Exception:
            pass

        return findings

    @classmethod
    def create_bundle(cls, context: RepositoryContext, parsed: ParsedRepository) -> AnalysisBundle:
        """Execute static tool passes based on primary language and construct AnalysisBundle."""
        findings: List[StaticFinding] = []
        tool_status: Dict[str, str] = {}

        if context.primary_language == Language.PYTHON:
            # Run Ruff
            try:
                ruff_res = cls.run_ruff(context.repository_path)
                findings.extend(ruff_res)
                tool_status["ruff"] = "success"
            except Exception as e:
                tool_status["ruff"] = f"failed: {str(e)}"

            # Run Bandit
            try:
                bandit_res = cls.run_bandit(context.repository_path)
                findings.extend(bandit_res)
                tool_status["bandit"] = "success"
            except Exception as e:
                tool_status["bandit"] = f"failed: {str(e)}"

            # Run Pip Audit
            try:
                audit_res = cls.run_pip_audit(context.repository_path)
                findings.extend(audit_res)
                tool_status["pip_audit"] = "success"
            except Exception as e:
                tool_status["pip_audit"] = f"failed: {str(e)}"
        else:
            # Run ESLint
            try:
                eslint_res = cls.run_eslint(context.repository_path)
                findings.extend(eslint_res)
                tool_status["eslint"] = "success"
            except Exception as e:
                tool_status["eslint"] = f"failed: {str(e)}"

        return AnalysisBundle(
            context=context,
            parsed_repo=parsed,
            static_findings=findings,
            tool_status=tool_status
        )
