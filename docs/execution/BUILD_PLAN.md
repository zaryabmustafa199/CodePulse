# CodePulse — Vertical Build Plan
**Principle:** Every week ends with a deployable, demo-able system. No exceptions.
**Anti-pattern this document prevents:** Building complete layers horizontally (full fetcher → full parser → full agent) which produces three complete components and zero working systems.

---

## The Vertical vs Horizontal Trap

**Horizontal (wrong):**
```
Week 1: Build complete Repository Fetcher (all edge cases, all validation)
Week 2: Build complete File Parser (all languages, full graph)
Week 3: Build complete Analysis Runner (all 6 tools)
Week 4: Build complete Agent Layer (all 6 agents)
Week 5: Build report UI
→ First working demo: Week 5
→ Problems discovered: Week 5
→ Time to fix: none left
```

**Vertical (correct):**
```
Week 1: One repo → one tool → one agent → one report section → visible in browser
Week 2: Expand to handle real repos reliably. Add second tool.
Week 3: Add remaining agents. Real report quality.
Week 4: Error handling, edge cases, performance.
Week 5: Polish, deploy, documentation.
→ First working demo: End of Week 1
→ Problems discovered: Week 1–3
→ Time to fix: Weeks 2–4
```

---

## Pre-Build Week (Days 1–7): Foundations

This week produces no product code. It produces decisions.

| Day | Task | Output |
|---|---|---|
| 1 | Run Spike 1 (dependency graph) | Decision document |
| 2 | Run Spike 1 continued | Decision document |
| 3 | Run Spike 1 continued + write decision | Spike 1 decision |
| 4 | Run Spike 2 (LLM quality) | Prompt experiments |
| 5 | Run Spike 2 continued + write decision | Spike 2 decision |
| 6 | Run Spike 3 (timing) + write decision | Spike 3 decision |
| 7 | Review all 3 decisions. Update interfaces document if needed. Make architecture decision (sync vs async). | Confirmed interfaces, confirmed architecture |

**Gate:** Do not proceed to Week 1 unless all 3 spike decision documents exist.

---

## Week 1 (Days 8–14): The First Vertical Slice

**Goal:** A human can submit one Python GitHub repository URL and see a real analysis report in a browser window.

**Scope deliberately minimal:**
- One language: Python only
- One static tool: Ruff only
- One agent: Code Quality agent only
- No database: results returned in the HTTP response, not stored
- No queue: synchronous processing
- No styling: plain HTML is fine

### Day 8-9: Repository Fetcher (minimal)

Build only what the first slice needs:

```python
# fetcher.py
def fetch_repository(github_url: str) -> RepositoryContext:
    # 1. Validate it's a GitHub URL
    # 2. Clone to temp directory
    # 3. Detect if it's Python (look for .py files and requirements.txt)
    # 4. Count files and lines
    # 5. Return RepositoryContext
    # Error if: not Python, over 15k lines, clone fails
```

Write one test:
```python
def test_fetch_valid_python_repo():
    ctx = fetch_repository("https://github.com/psf/requests")
    assert ctx.primary_language == Language.PYTHON
    assert ctx.total_files > 0
    assert ctx.error is None
```

### Day 10: File Parser (minimal)

Build only what the Code Quality agent needs — file list and basic metrics. Skip the dependency graph for now (that comes in Week 3).

```python
# parser.py
def parse_repository(ctx: RepositoryContext) -> ParsedRepository:
    # 1. Walk .py files
    # 2. Count lines, functions, classes per file using ast module
    # 3. Return ParsedRepository with source_files populated
    # Skip import graph for now — placeholder empty list
```

### Day 11: Analysis Runner (Ruff only)

```python
# runner.py
def run_analysis(parsed: ParsedRepository) -> AnalysisBundle:
    # 1. Run: ruff check {local_path} --output-format=json
    # 2. Parse JSON output into List[StaticIssue]
    # 3. Return AnalysisBundle
    # Handle: ruff not installed, ruff fails, ruff times out (30s max)
```

### Day 12: Code Quality Agent (one LLM call)

```python
# agents/code_quality.py
def run_code_quality_agent(bundle: AnalysisBundle) -> AgentFinding:
    # 1. Build a structured summary of Ruff findings (counts by category, worst files)
    # 2. Call Gemini API with system prompt + structured summary
    # 3. Parse response into AgentFinding
    # 4. Return AgentFinding with domain=CODE_QUALITY
```

### Day 13: Report Compiler + Basic API

```python
# compiler.py
def compile_report(findings: List[AgentFinding], bundle: AnalysisBundle) -> EngineeringReport:
    # Build EngineeringReport from whatever findings exist

# main.py (FastAPI)
@app.post("/api/v1/analyze")
async def analyze(github_url: str) -> EngineeringReport:
    ctx = fetch_repository(github_url)
    parsed = parse_repository(ctx)
    bundle = run_analysis(parsed)
    findings = [run_code_quality_agent(bundle)]
    return compile_report(findings, bundle)
```

### Day 14: Basic Frontend

One HTML page with:
- A URL input field
- A submit button
- A loading state ("Analyzing... this may take up to 3 minutes")
- A results section that renders the JSON report

No framework needed yet. Plain HTML + JavaScript fetch() is fine.

**End of Week 1 checkpoint:**
You can submit `https://github.com/psf/requests` and see a Code Quality report in your browser. It might be slow. The report might not look great. That's fine. It works.

---

## Week 2 (Days 15–21): Harden and Expand

**Goal:** The system works reliably on diverse real repos, not just the happy path.

### Error Handling Pass (Days 15–16)

Go through every function you wrote in Week 1 and handle every failure case:

- Repository does not exist → 404 with clear message
- Repository is private → clear message
- Repository has no Python files → clear message
- Ruff fails to run → partial report, mark tool as failed
- Gemini API times out → retry once, then return error
- Clone takes more than 60 seconds → abort with timeout error
- Cleanup: ensure temp directory is always deleted after analysis

Write tests for at least 3 error cases.

### Add Second Static Tool: Bandit (Days 17–18)

```python
# In runner.py, add alongside Ruff:
def run_bandit(local_path: str) -> StaticToolResult:
    # subprocess: bandit -r {local_path} -f json
    # parse output into StaticToolResult
```

Update the Code Quality agent prompt to include security findings from Bandit.

Add the Security agent as a second agent using the Bandit output.

### Async Processing (Day 19)

If Spike 3 showed that analysis takes more than 60 seconds on a medium repo, implement async processing now:

```python
# Return immediately with analysis_id
@app.post("/api/v1/analyze")
async def start_analysis(github_url: str):
    analysis_id = str(uuid4())
    background_tasks.add_task(run_full_analysis, analysis_id, github_url)
    return {"analysis_id": analysis_id, "status": "pending"}

# Poll for results
@app.get("/api/v1/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    # Read from in-memory dict for now (database comes in Week 3)
    return analysis_store.get(analysis_id)
```

Frontend: update to poll every 5 seconds until status is "complete".

### Add TypeScript/JavaScript Support (Days 20–21)

Add ESLint as a third static tool for JS/TS repos.
Update the Fetcher to detect JS/TS repos.
Update the Parser to handle `.ts`, `.tsx`, `.js`, `.jsx` files.

**End of Week 2 checkpoint:**
System handles Python and TypeScript repos. Returns partial results instead of crashing when tools fail. Async polling works.

---

## Week 3 (Days 22–28): Full Agent Suite

**Goal:** All 6 analysis domains produce findings. Dependency graph working.

### Dependency Graph (Days 22–23)

Implement the Tree-sitter dependency graph from Spike 1 decisions.
Update the File Parser to populate `import_edges` and `circular_dependencies`.
Update the Architecture agent to use this graph.

### Remaining 4 Agents (Days 24–26)

Add in this order:
1. **Architecture Agent** — uses dependency graph + folder structure
2. **Documentation Agent** — uses README word count, docstring coverage, API docs detection
3. **Dependency Agent** — uses pip-audit / npm audit output
4. **Overview Agent** — runs last, has access to all other findings to produce the executive summary

### Database: PostgreSQL (Day 27)

Replace the in-memory `analysis_store` dict with a real database.

Two tables only:
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    repository_url TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE reports (
    analysis_id UUID REFERENCES analyses(id),
    report_json JSONB NOT NULL
);
```

### Parallel Agent Execution (Day 28)

Run all 6 agents concurrently:
```python
import asyncio

async def run_all_agents(bundle: AnalysisBundle) -> List[AgentFinding]:
    tasks = [
        run_overview_agent(bundle),
        run_architecture_agent(bundle),
        run_code_quality_agent(bundle),
        run_security_agent(bundle),
        run_documentation_agent(bundle),
        run_dependency_agent(bundle),
    ]
    return await asyncio.gather(*tasks)
```

**End of Week 3 checkpoint:**
Submit any Python or TypeScript repo and receive a full 6-section report. Findings are stored in the database. Multiple requests don't block each other.

---

## Week 4 (Days 29–35): Quality and Reliability

**Goal:** The system produces high-quality output on repos you've never seen before.

### Manual Quality Audit + Golden Test Set (Days 29–30)

**Step 1 — Build the golden test set first.**

Before running any analysis, choose 10 real public repositories and write down what you already know about each one manually. Example:

```
golden_test_set.md

Repo 1: https://github.com/tiangolo/fastapi
Known: Excellent documentation, clean architecture, no obvious security issues
Expected grades: Architecture A, Docs A, Security B+

Repo 2: https://github.com/[a messy student project you know]
Known: No tests, README is empty, hardcoded credentials in config
Expected grades: Security D, Docs F, Testing F
...
```

Save this file. This is your regression baseline. Every time you change a prompt, re-run these 10 repos and compare results. If a repo that scored B starts scoring D after a prompt change, something broke.

**Step 2 — Run analysis on all 10 and grade every finding:**
- **Correct and specific:** Finding is accurate and mentions actual files/metrics from this project
- **Correct but generic:** Finding is true but identical wording would fit any project
- **Wrong:** Finding is inaccurate or not traceable to the static analysis data

Target: Less than 20% generic, 0% wrong. Improve prompts until you hit this target.

**Step 3 — Increment prompt versions when you make changes.**

Each time you edit a prompt, update the `prompt_version` string in that agent (e.g. `"architecture-v1"` → `"architecture-v2"`). Never reuse a version string. After changing a prompt, re-run the full golden test set and note whether specificity improved or regressed. Keep a one-line changelog:

```
prompt_changelog.md
architecture-v1: initial
architecture-v2: added instruction to cite file paths in every finding → specificity +15%
architecture-v3: removed folder structure from input (too noisy) → reduced hallucinations
```

This takes 10 minutes per change but saves hours of confusion when you can't remember why a report looks different.

### Rate Limiting and Abuse Prevention (Day 31)

```python
# In-memory rate limiter: 3 analyses per IP per hour
from collections import defaultdict
from datetime import datetime, timedelta

request_log: dict[str, list[datetime]] = defaultdict(list)

def check_rate_limit(ip: str) -> bool:
    now = datetime.utcnow()
    recent = [t for t in request_log[ip] if now - t < timedelta(hours=1)]
    request_log[ip] = recent
    return len(recent) < 3
```

### Repository Size Enforcement (Day 32)

Enforce all validation rules from the Interfaces document before cloning.
Use GitHub API to check repo size before cloning (avoid wasting time).

### Logging and Monitoring (Days 33–34)

Add structured logging to every component:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("analysis_started", extra={"analysis_id": id, "url": url})
logger.info("stage_complete", extra={"stage": "fetcher", "duration": t})
logger.error("tool_failed", extra={"tool": "bandit", "error": str(e)})
```

### Temp File Cleanup (Day 35)

Ensure every cloned repository is deleted after analysis — even if analysis crashes:
```python
import tempfile
import shutil

with tempfile.TemporaryDirectory() as tmpdir:
    try:
        run_analysis(tmpdir)
    finally:
        # TemporaryDirectory context manager handles this
        # But verify it works even on exception
        pass
```

**End of Week 4 checkpoint:**
System handles malformed URLs, huge repos, unsupported languages, tool failures, and rate limit abuse — without crashing. Report quality is consistently good on unfamiliar repos.

---

## Week 5 (Days 36–40): Polish and Deploy

### Report UI (Days 36–37)

Build the proper frontend using Next.js + Tailwind:
- Score cards for each of the 6 domains
- Expandable findings sections
- Tech stack badges
- Overall score with grade
- Download as JSON button

### README and Documentation (Day 38)

Write a README that covers:
- What the project does (one paragraph)
- Architecture diagram (draw.io or mermaid)
- How to run locally (step by step, tested on a clean machine)
- Tech stack and why each tool was chosen
- Known limitations

### Deploy (Day 39)

- Backend: Railway or Render (FastAPI + PostgreSQL)
- Frontend: Vercel (Next.js)
- Environment variables: documented in `.env.example`

### Demo Video (Day 40)

Record a 3-minute screen recording:
1. Submit a real GitHub repo
2. Watch the analysis run
3. Walk through the report findings
4. Explain one interesting architectural decision you made

Upload to YouTube. Link in README.

**Final checkpoint:**
Public URL works. Anyone can submit a repo. Report looks professional. README explains the project clearly to a technical interviewer.

---

## Next Phase Extension Build Plan (Phases 2, 3, & 4)

### Phase 2: Next.js 14 Web UI (Option A)
- **Goal**: Full Next.js 14 App Router UI with Glassmorphism Theme.
- **Deliverables**: Recharts 6-axis Radar Chart, Score Cards, Accordions, PDF/JSON export.

### Phase 3: Enterprise Database & Redis Upgrade (Option B)
- **Goal**: Database Adapter pattern + Redis rate limiting.
- **Deliverables**: Abstract `DatabaseProvider` (SQLite local + PostgreSQL `JSONB` cloud), Redis sliding window limiter.

### Phase 4: Real-Time SSE Progress Streaming (Option C)
- **Goal**: Live streaming progress updates during multi-agent analysis.
- **Deliverables**: `GET /api/v1/analyze/stream` SSE endpoint + Next.js EventSource real-time progress bar.

---

## Weekly Deliverable Checklist

| Week | Must have by end of week |
|---|---|
| Pre-build | 3 spike decision documents. Interfaces document finalized. |
| Week 1 | Working end-to-end for one Python repo. Basic UI. |
| Week 2 | Error handling. Two languages. Async polling. |
| Week 3 | All 6 agents. Database. Parallel execution. |
| Week 4 | Quality audit passed. Rate limiting. Logging. |
| Week 5 | Deployed. README complete. Demo video recorded. |
| Phase 2 | Next.js 14 Web UI (Glassmorphism Dashboard & Recharts Radar Graph). |
| Phase 3 | PostgreSQL JSONB & Redis Rate Limiting Adapter Upgrade. |
| Phase 4 | Server-Sent Events (SSE) Real-Time Analysis Progress Streaming. |

If you miss a weekly deliverable, **do not add scope to catch up.** Cut the lowest-priority feature of the next week instead.
