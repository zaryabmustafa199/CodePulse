"""
Canonical Pydantic v2 Data Models for CodePulse.
Defined per INTERFACES.md specifications.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


class Framework(str, Enum):
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    REACT = "react"
    EXPRESS = "express"
    UNKNOWN = "unknown"


class AgentDomain(str, Enum):
    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    DEPENDENCY = "dependency"


class RepositoryContext(BaseModel):
    repository_path: str
    primary_language: Language = Language.PYTHON
    framework: Framework = Framework.UNKNOWN
    total_files: int = 0
    total_lines: int = 0
    file_manifest: List[str] = Field(default_factory=list)
    readme_content: Optional[str] = None
    dependency_file_raw: Optional[str] = None
    error: Optional[str] = None


class FileMetrics(BaseModel):
    relative_path: str
    line_count: int
    function_count: int = 0
    class_count: int = 0
    docstring_count: int = 0


class ImportEdge(BaseModel):
    source_file: str
    target_file: str
    is_resolved: bool = True
    is_third_party: bool = False


class ParsedRepository(BaseModel):
    source_files: Dict[str, FileMetrics] = Field(default_factory=dict)
    import_edges: List[ImportEdge] = Field(default_factory=list)
    circular_dependencies: List[List[str]] = Field(default_factory=list)
    most_imported_files: List[tuple] = Field(default_factory=list)
    folder_structure: Dict[str, int] = Field(default_factory=dict)
    parse_duration_seconds: float = 0.0


class StaticFinding(BaseModel):
    tool_name: str
    rule_id: str
    message: str
    file_path: str
    line_number: int
    severity: str = "medium"  # high, medium, low
    category: str = "code_quality"  # code_quality, security, style


class AnalysisBundle(BaseModel):
    context: RepositoryContext
    parsed_repo: ParsedRepository
    static_findings: List[StaticFinding] = Field(default_factory=list)
    tool_status: Dict[str, str] = Field(default_factory=dict)  # {"ruff": "success"}


class AgentFinding(BaseModel):
    domain: AgentDomain
    score: Optional[int] = Field(default=None, ge=1, le=10)
    score_rationale: str = ""
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: str = "high"  # high, medium, low, none
    prompt_version: str = "v1"


class AnalysisRequest(BaseModel):
    repository_path: str = Field(..., description="Absolute local path or repo directory to analyze")


class EngineeringReport(BaseModel):
    analysis_id: Optional[str] = None
    status: str = "success"
    total_latency_seconds: float = 0.0
    overall_score: Optional[int] = None
    overall_grade: str = "N/A"
    executive_summary: str = ""
    repository_path: str = ""
    primary_language: str = "python"
    total_files: int = 0
    total_lines: int = 0
    domain_findings: Dict[str, AgentFinding] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
