# CodePulse — Interface Definitions
**Purpose:** Define every data contract between components before writing implementation code.
**Rule:** No implementation file is written until the interface it produces or consumes is defined here. If you cannot define the output of a component, you do not understand what it does — redesign first.

---

## Why Interfaces First

Every bug that crosses a component boundary is an interface contract violation. If the File Parser produces a dict and the Analysis Runner expects a dataclass, that is a bug you introduced by skipping this document. Writing interfaces first forces you to think about what each component actually does rather than how it does it.

---

## Component Map

```
GitHub URL
    │
    ▼
[1. Repository Fetcher]
    │ RepositoryContext
    ▼
[2. File Parser]
    │ ParsedRepository
    ▼
[3. Analysis Runner]
    │ AnalysisBundle
    ▼
[4. Agent Layer] ──── 6 agents run in parallel
    │ List[AgentFinding]
    ▼
[5. Report Compiler]
    │ EngineeringReport
    ▼
JSON / HTML Response
```

---

## Python Dataclass Definitions

All backend interfaces are defined as Python dataclasses. These are the canonical definitions. If you change one, update this document first.

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

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
    NEXTJS = "nextjs"
    EXPRESS = "express"
    NONE = "none"
    UNKNOWN = "unknown"

class AgentDomain(str, Enum):
    OVERVIEW = "overview"
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    DEPENDENCIES = "dependencies"

class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


# ─────────────────────────────────────────────
# COMPONENT 1: REPOSITORY FETCHER OUTPUT
# ─────────────────────────────────────────────

@dataclass
class RepositoryContext:
    """
    Output of the Repository Fetcher.
    Everything downstream needs to know about the repo before touching files.
    """
    # Identity
    url: str                          # Original submitted URL
    owner: str                        # GitHub username/org
    repo_name: str                    # Repository name
    default_branch: str               # "main" or "master"
    local_path: str                   # Absolute path to cloned directory on disk

    # Size and limits
    total_files: int                  # Total file count (all types)
    total_lines: int                  # Total lines of code (source files only)
    total_size_mb: float              # Total repository size in MB

    # Language detection
    primary_language: Language        # Dominant language detected
    languages_detected: list[str]     # All languages found (e.g. ["python", "html", "css"])

    # Framework detection
    primary_framework: Framework      # Most likely framework
    has_dockerfile: bool
    has_ci_config: bool               # .github/workflows, .gitlab-ci.yml, etc.
    has_tests: bool                   # Any test directory or test files found
    has_readme: bool
    has_license: bool
    has_gitignore: bool

    # Metadata
    fetched_at: datetime
    clone_duration_seconds: float

    # Error handling
    error: Optional[str] = None       # None if successful, error message if failed


# ─────────────────────────────────────────────
# COMPONENT 2: FILE PARSER OUTPUT
# ─────────────────────────────────────────────

@dataclass
class ImportEdge:
    """A single import relationship between two files."""
    source_file: str                  # Relative path of importing file
    imported_target: str              # Resolved relative path, or raw import string if unresolved
    is_resolved: bool                 # True if we found the actual file on disk
    is_third_party: bool              # True if it's a package (not a local project file)

@dataclass
class FileMetrics:
    """Per-file metrics collected during parsing."""
    relative_path: str
    language: Language
    line_count: int
    function_count: int               # Number of function/method definitions
    class_count: int                  # Number of class definitions
    max_function_length: int          # Lines in longest function
    has_docstrings: bool              # At least one docstring present
    imports: list[str]                # Raw import statements

@dataclass
class ParsedRepository:
    """
    Output of the File Parser.
    Contains structural understanding of the codebase — no static analysis results yet.
    """
    context: RepositoryContext        # Pass-through from fetcher

    # File inventory
    source_files: list[FileMetrics]   # All analyzed source files
    total_functions: int
    total_classes: int

    # Dependency graph
    import_edges: list[ImportEdge]
    circular_dependencies: list[list[str]]  # Each inner list is a cycle
    most_imported_files: list[str]    # Top 5 by in-degree, relative paths

    # Structure signals
    folder_structure: dict            # {folder_name: file_count} for top 2 levels
    largest_files: list[str]          # Top 5 files by line count, relative paths
    estimated_architecture_pattern: str  # "MVC", "Layered", "Monolith", "Unknown"

    # Timing
    parse_duration_seconds: float


# ─────────────────────────────────────────────
# COMPONENT 3: ANALYSIS RUNNER OUTPUT
# ─────────────────────────────────────────────

@dataclass
class StaticIssue:
    """A single issue found by a static analysis tool."""
    tool: str                         # "ruff", "bandit", "semgrep", "eslint"
    rule_id: str                      # Tool-specific rule identifier
    message: str                      # Human-readable description
    file_path: str                    # Relative path
    line_number: int
    severity: Severity
    category: str                     # "style", "security", "complexity", "unused", etc.

@dataclass
class StaticToolResult:
    """Output from a single static analysis tool run."""
    tool: str
    ran_successfully: bool
    issues: list[StaticIssue]
    issue_count: int
    run_duration_seconds: float
    error_message: Optional[str] = None

@dataclass
class DependencyIssue:
    """A single problematic dependency."""
    package_name: str
    current_version: str
    issue_type: str                   # "vulnerable", "outdated", "abandoned", "deprecated"
    severity: Severity
    description: str
    recommended_version: Optional[str] = None

@dataclass
class AnalysisBundle:
    """
    Output of the Analysis Runner.
    All raw findings from deterministic tools — no LLM involvement yet.
    """
    parsed_repo: ParsedRepository     # Pass-through from parser

    # Static analysis results
    static_results: list[StaticToolResult]

    # Aggregated issue counts by category
    issues_by_severity: dict[str, int]    # {"high": 3, "medium": 12, "low": 45}
    issues_by_category: dict[str, int]    # {"security": 3, "style": 40, "complexity": 12}
    most_problematic_files: list[str]     # Top 5 files with most issues

    # Documentation signals
    readme_word_count: int
    has_api_docs: bool                # openapi.json, swagger, docstrings in route handlers
    docstring_coverage_estimate: float  # % of functions with docstrings (0.0–1.0)
    inline_comment_density: float     # Comments per 100 lines

    # Dependency analysis
    dependency_issues: list[DependencyIssue]
    total_dependencies: int
    vulnerable_count: int
    outdated_count: int

    # Timing
    analysis_duration_seconds: float


# ─────────────────────────────────────────────
# COMPONENT 4: AGENT LAYER OUTPUT
# ─────────────────────────────────────────────

@dataclass
class AgentFinding:
    """
    Output of a single specialized agent.
    This is what the LLM produces — an interpretation of the raw analysis data.
    """
    domain: AgentDomain
    score: int                        # 1–10 (1 = very poor, 10 = excellent)
    score_rationale: str              # One sentence explaining the score
    summary: str                      # 2–3 sentences: overall assessment of this domain
    strengths: list[str]              # Specific positive findings (2–4 items)
    risks: list[str]                  # Specific concerns (2–4 items)
    recommendations: list[str]        # Actionable next steps, prioritized (2–3 items)
    confidence: str                   # "high", "medium", "low"
    agent_duration_seconds: float
    prompt_version: str               # e.g. "architecture-v3". Increment when prompt changes.
                                      # Format: "{domain}-v{N}". Never reuse a version string.
                                      # Purpose: lets you trace which prompt produced a report
                                      # and detect quality regressions after prompt edits.

    # The agent must not fabricate. Every finding must be grounded in:
    # - A specific file path, OR
    # - A static tool result, OR
    # - A measurable metric from the AnalysisBundle
    # If the agent cannot ground a finding, it must not include it.


# ─────────────────────────────────────────────
# COMPONENT 5: REPORT COMPILER OUTPUT
# ─────────────────────────────────────────────

# Score weights used by the Report Compiler. These are fixed for v1.
# Change requires a PRD amendment, not just a code edit.
DOMAIN_WEIGHTS: dict[AgentDomain, float] = {
    AgentDomain.ARCHITECTURE:  0.25,
    AgentDomain.CODE_QUALITY:  0.20,
    AgentDomain.SECURITY:      0.20,
    AgentDomain.DEPENDENCIES:  0.15,
    AgentDomain.DOCUMENTATION: 0.10,
    AgentDomain.OVERVIEW:      0.10,
}
# Overall score = sum(finding.score * DOMAIN_WEIGHTS[finding.domain] for finding in findings)

@dataclass
class ReportSummary:
    """The top-level executive summary of the report."""
    overall_score: float              # Weighted score using DOMAIN_WEIGHTS above
    overall_grade: str                # A(9-10), B(7-8.9), C(5-6.9), D(3-4.9), F(1-2.9)
    top_strengths: list[str]          # Best 3 findings across all agents
    top_risks: list[str]              # Worst 3 findings across all agents
    top_recommendations: list[str]    # Most impactful 3 actions to take
    one_paragraph_summary: str        # Plain-English summary a non-expert can read

@dataclass
class EngineeringReport:
    """
    Final output of the system. This is what the API returns and the UI renders.
    """
    # Identity
    analysis_id: str                  # UUID
    repository_url: str
    repository_name: str
    analyzed_at: datetime

    # Results
    summary: ReportSummary
    agent_findings: list[AgentFinding]  # 6 findings, one per domain

    # Raw metadata for display
    tech_stack: list[str]             # ["React", "FastAPI", "PostgreSQL", "Docker"]
    total_files_analyzed: int
    total_lines_analyzed: int
    primary_language: str
    primary_framework: str

    # Cache key fields
    commit_sha: str                   # Latest commit SHA at time of analysis (from GitHub API)
                                      # Cache key = repository_url + commit_sha

    # Timing
    total_duration_seconds: float
    status: AnalysisStatus
    served_from_cache: bool = False   # True if returned from cache, not re-analyzed

    # Error handling
    failed_tools: list[str]           # Tools that errored out (analysis may be partial)
    error_message: Optional[str] = None
```

---

## API Request/Response Contracts

### POST /api/v1/analyze

**Confirmed Architecture:** Synchronous HTTP (Spike 3 decision: Total parallel latency is 3.21s < 15.0s boundary).

**Request:**
```json
{
  "github_url": "https://github.com/owner/repository"
}
```

**Response (200 OK — Analysis Complete Direct Response):**
```json
{
  "status": "success",
  "total_latency_seconds": 3.21,
  "report": { /* Full EngineeringReport as JSON */ }
}
```

**Error Responses:**
```json
{ "error": "invalid_url", "message": "URL must be a valid public GitHub repository." }
{ "error": "repo_too_large", "message": "Repository exceeds 15,000 line limit for v1." }
{ "error": "unsupported_language", "message": "Only Python and TypeScript/JavaScript repos are supported in v1." }
{ "error": "rate_limited", "message": "Please wait 60 seconds before submitting another analysis." }
```

---

## Validation Rules

These rules are enforced at the Repository Fetcher layer before any analysis begins.

| Rule | Limit | Reason |
|---|---|---|
| Max repository size | 50 MB | Cloning time and disk usage |
| Max lines of code | 15,000 (counted lines only — see exclusions below) | Processing time guarantee |
| Max file count | 500 source files | Parser performance |
| Max single file size | 2,000 lines — files exceeding this are skipped as likely generated | Prevents minified/bundled files from distorting analysis |
| Excluded paths | `node_modules/`, `dist/`, `build/`, `.git/`, `__pycache__/` | Generated/dependency content, not project source |
| Excluded file patterns | `*.min.js`, `*.min.css`, `*.lock`, `*.snap`, `*.pb.go`, `*_generated.*` | Minified, lockfile, or auto-generated files |
| Supported languages | Python, TypeScript, JavaScript only | v1 scope |
| Repository must be public | Yes | No OAuth in v1 |
| URL must be a valid GitHub URL | Yes | Only GitHub supported in v1 |
| Rate limit per IP | 3 analyses per hour | Cost and abuse prevention |

---

## Next Phase Interface Extensions (Phases 2, 3, & 4)

### Phase 2: Next.js Frontend Component Contract
The frontend React components consume `EngineeringReport` JSON from FastAPI:

```typescript
// Component Props Interfaces
interface ScoreRadarChartProps {
  domainFindings: Record<string, AgentFinding>;
}

interface DomainScoreCardProps {
  domainKey: string;
  finding: AgentFinding;
}

interface FindingsAccordionProps {
  findings: AgentFinding[];
}
```

### Phase 3: Database Adapter Contract (`src/backend/db.py`)
```python
from abc import ABC, abstractmethod

class DatabaseAdapter(ABC):
    @abstractmethod
    async def init_db(self) -> None: ...
    
    @abstractmethod
    async def save_analysis(self, analysis_id: str, repo_path: str, report_dict: dict) -> None: ...
    
    @abstractmethod
    async def get_report(self, analysis_id: str) -> Optional[dict]: ...
```

### Phase 4: Server-Sent Events (SSE) Streaming Contract
Endpoint: `GET /api/v1/analyze/stream?repository_path={path}`

Stream Event Payload (`text/event-stream`):
```json
event: progress
data: {
  "stage": "fetcher" | "parser" | "static_runner" | "parallel_agents" | "overview_agent",
  "progress_pct": 20 | 40 | 60 | 80 | 100,
  "message": "Step description string"
}
```

---

## Interface Change Protocol

If you need to change any interface defined in this document:

1. Update this document first.
2. List what broke (which components are affected).
3. Update all affected components.
4. Update the corresponding tests.

Never change an implementation to produce a different output shape without updating this document. This document is the source of truth, not the code.
