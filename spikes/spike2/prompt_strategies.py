"""
Spike 2: Prompt Strategy Builders & System Prompt Specs.
Defines payload formats for Prompt Strategies A, B, and C as specified in SPIKES.md,
including the mandatory GROUNDING RULE from CONSTITUTION.md.
"""

import json
from typing import Dict, Any, Tuple

GROUNDING_RULE_VERBATIM = """GROUNDING RULE:
Every finding you report must be traceable to one of:
1. A specific file path in the repository
2. A specific result from the static analysis tools provided
3. A specific measurable metric (line count, function count, issue count, etc.)

If you cannot ground a finding in one of these three sources, write:
UNKNOWN — [brief reason why evidence is insufficient]

Never infer. Never guess. Never extrapolate beyond the data provided.
A confident wrong answer is worse than an honest UNKNOWN."""


class PromptStrategyBuilder:
    """Builds prompt payloads for testing LLM quality strategies A, B, and C."""
    
    @staticmethod
    def build_strategy_a(raw_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Strategy A — Dump Everything:
        Raw tool log strings, directory tree, full file list, raw outputs.
        """
        system_prompt = "You are a senior software engineer. Analyze the following raw static tool dumps and project directory data to produce an architecture and quality assessment."
        
        user_prompt = f"""PROJECT FILE INVENTORY:
{json.dumps(raw_data.get('file_inventory', []), indent=2)}

DIRECTORY TREE:
{json.dumps(raw_data.get('folder_structure', {}), indent=2)}

DEPENDENCIES:
{json.dumps(raw_data.get('dependencies', []), indent=2)}

RAW RUFF OUTPUT:
{json.dumps(raw_data.get('raw_ruff_issues', []), indent=2)}

RAW BANDIT OUTPUT:
{json.dumps(raw_data.get('raw_bandit_issues', []), indent=2)}

RAW ESLINT OUTPUT:
{json.dumps(raw_data.get('raw_eslint_issues', []), indent=2)}

Please provide a full quality assessment with strengths, risks, recommendations, and domain scores.
"""
        return system_prompt, user_prompt

    @staticmethod
    def build_strategy_b(summary_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Strategy B — Structured Summary First:
        Pre-summarizes issue counts by category, severity distribution, and top-affected files.
        """
        system_prompt = "You are an engineering intelligence agent. Analyze this pre-summarized project quality metrics bundle and return structured recommendations."
        
        user_prompt = f"""SUMMARY OF METRICS:
- Total Source Files: {summary_data.get('total_files')}
- Total Lines of Code: {summary_data.get('total_lines')}
- Language Breakdown: {json.dumps(summary_data.get('languages', {}))}

ISSUES BY SEVERITY:
{json.dumps(summary_data.get('issues_by_severity', {}), indent=2)}

ISSUES BY CATEGORY:
{json.dumps(summary_data.get('issues_by_category', {}), indent=2)}

TOP 5 MOST PROBLEMATIC FILES:
{json.dumps(summary_data.get('most_problematic_files', []), indent=2)}

DEPENDENCY AUDIT:
- Total Dependencies: {summary_data.get('total_dependencies')}
- Vulnerable Packages: {summary_data.get('vulnerable_count')}
- Outdated Packages: {summary_data.get('outdated_count')}

GRAPH ARCHITECTURE SIGNALS:
- Top Imported Files: {json.dumps(summary_data.get('top_imported_files', []), indent=2)}
- Circular Dependency Cycles: {summary_data.get('circular_cycle_count')}

Please assess the codebase performance across Architecture, Security, and Code Quality.
"""
        return system_prompt, user_prompt

    @staticmethod
    def build_strategy_c(domain: str, domain_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Strategy C — Domain-Specific Context with Verbatim GROUNDING RULE:
        Sends only target-domain findings + exact AgentFinding JSON schema constraints.
        """
        system_prompt = f"""You are the CodePulse {domain.upper()} Agent. Your sole responsibility is to produce a grounded engineering assessment for the {domain} domain.

{GROUNDING_RULE_VERBATIM}

You MUST return your finding strictly as a JSON object matching this schema:
{{
  "domain": "{domain}",
  "score": 1-10,
  "score_rationale": "One sentence rationale",
  "summary": "2-3 sentence overview",
  "strengths": ["grounded strength 1", "grounded strength 2"],
  "risks": ["grounded risk 1", "grounded risk 2"],
  "recommendations": ["actionable step 1", "actionable step 2"],
  "confidence": "high|medium|low"
}}
"""

        user_prompt = f"""DOMAIN ANALYSIS BUNDLE ({domain.upper()}):

METRICS & STATIC FINDINGS:
{json.dumps(domain_data, indent=2)}

Provide your grounded JSON analysis according to the system prompt rules.
"""
        return system_prompt, user_prompt
