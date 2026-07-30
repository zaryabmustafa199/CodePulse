"""
CodePulse Main FastAPI Application.
Exposes synchronous HTTP API endpoint POST /api/v1/analyze per INTERFACES.md specifications,
and GET /api/v1/analysis/{analysis_id} for database record retrieval.
"""

import time
import asyncio
from uuid import uuid4
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.backend.config import settings
from src.backend.models.schemas import (
    AnalysisRequest,
    EngineeringReport,
    AgentFinding,
    AgentDomain
)
from src.backend.services.fetcher import RepositoryFetcher
from src.backend.services.parser import TreeSitterParserService
from src.backend.services.runner import AnalysisRunnerService
from src.backend.services.agents import LLMAgentService
from src.backend.db import init_db, save_analysis_record, get_analysis_report
from src.backend.logger import log_event
from src.backend.middleware.rate_limiter import IPRateLimiterMiddleware

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables at application startup."""
    init_db()
    if settings.DEV_MODE:
        log_event("application_startup", status="initialized", warning="DEV_MODE=true — rate limit is relaxed to 100 req/hr. Do NOT deploy with this setting.")
    else:
        log_event("application_startup", status="initialized")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CodePulse Engineering Intelligence Platform Backend API",
    lifespan=lifespan
)

# Enable Rate Limiting & CORS
rate_limit_max = 100 if settings.DEV_MODE else 3
app.add_middleware(IPRateLimiterMiddleware, max_requests=rate_limit_max, window_seconds=3600)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy"
    }


@app.post(
    f"{settings.API_V1_STR}/analyze",
    response_model=EngineeringReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze a code repository synchronously and return EngineeringReport"
)
async def analyze_repository(request: AnalysisRequest) -> EngineeringReport:
    """
    Execute full multi-agent analysis pipeline:
    Fetcher -> Tree-sitter Parser -> Static Runner -> 5 Domain Agents Parallel -> Overview Agent -> SQLite Persist.
    """
    start_time = time.time()
    created_at = datetime.now(timezone.utc).isoformat()
    analysis_id = str(uuid4())
    repo_path = request.repository_path.strip()

    LLMAgentService.reset_circuit_breaker()
    log_event("analysis_started", analysis_id=analysis_id, repository_path=repo_path)

    # 1. Fetcher & Validation
    context = RepositoryFetcher.fetch_repository(repo_path)
    if context.error:
        log_event("fetcher_failed", level="error", analysis_id=analysis_id, error=context.error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=context.error
        )

    # 2. Parser & AST Graph
    parser_service = TreeSitterParserService(context)
    parsed_repo = parser_service.parse()

    # 3. Static Tool Runner (Ruff, Bandit, ESLint, pip-audit)
    bundle = AnalysisRunnerService.create_bundle(context, parsed_repo)

    # 4. Run 5 Domain Agents in PARALLEL across two independent providers:
    #    Gemini   → Architecture, Security        (3 calls/analysis vs 6 before)
    #    OpenRouter → Code Quality, Documentation, Dependency  (independent quota pool)
    #    asyncio.gather fires all 5 simultaneously — total time = slowest agent, not sum
    arch_res, quality_res, sec_res, doc_res, dep_res = await asyncio.gather(
        LLMAgentService.run_architecture_agent(bundle),
        LLMAgentService.run_code_quality_agent(bundle),
        LLMAgentService.run_security_agent(bundle),
        LLMAgentService.run_documentation_agent(bundle),
        LLMAgentService.run_dependency_agent(bundle),
    )

    domain_findings = {
        AgentDomain.ARCHITECTURE.value: arch_res,
        AgentDomain.CODE_QUALITY.value: quality_res,
        AgentDomain.SECURITY.value: sec_res,
        AgentDomain.DOCUMENTATION.value: doc_res,
        AgentDomain.DEPENDENCY.value: dep_res,
    }

    # 5. Overview Agent runs after domain agents complete (needs their output to synthesize)
    overview_res = await LLMAgentService.run_overview_agent(bundle, domain_findings)
    domain_findings[AgentDomain.OVERVIEW.value] = overview_res

    # 6. Report Consolidation & Scoring
    total_latency = round(time.time() - start_time, 4)
    completed_at = datetime.now(timezone.utc).isoformat()

    valid_scores = [f.score for f in domain_findings.values() if f.score is not None]
    overall_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 8

    # Compute letter grade from score (1-10 scale)
    if overall_score >= 9:
        grade = "A"
    elif overall_score >= 8:
        grade = "B"
    elif overall_score >= 7:
        grade = "C"
    elif overall_score >= 6:
        grade = "D"
    else:
        grade = "F"

    report = EngineeringReport(
        analysis_id=analysis_id,
        status="success",
        total_latency_seconds=total_latency,
        overall_score=overall_score,
        overall_grade=grade,
        executive_summary=overview_res.summary,
        repository_path=context.repository_path,
        primary_language=context.primary_language.value,
        total_files=context.total_files,
        total_lines=context.total_lines,
        domain_findings=domain_findings
    )

    # 7. Persist analysis & report asynchronously into SQLite
    await save_analysis_record(
        analysis_id=analysis_id,
        repo_path=context.repository_path,
        status="success",
        created_at=created_at,
        completed_at=completed_at,
        latency_seconds=total_latency,
        report_dict=report.model_dump()
    )

    log_event(
        "analysis_completed",
        analysis_id=analysis_id,
        total_latency_seconds=total_latency,
        overall_score=overall_score,
        overall_grade=grade
    )

    return report


@app.post(
    f"{settings.API_V1_STR}/analyze/stream",
    summary="Analyze a code repository with real-time Server-Sent Events (SSE) streaming"
)
async def analyze_repository_stream(request: AnalysisRequest):
    """
    Execute multi-agent analysis pipeline with real-time Server-Sent Events (SSE) streaming.
    Yields step-by-step progress events, individual domain findings as they finish, and final report JSON.
    """
    import json
    from fastapi.responses import StreamingResponse

    repo_path = request.repository_path.strip()

    async def event_generator():
        start_time = time.time()
        created_at = datetime.now(timezone.utc).isoformat()
        analysis_id = str(uuid4())

        LLMAgentService.reset_circuit_breaker()
        def make_sse(event: str, data: any) -> str:
            payload = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
            return f"event: {event}\ndata: {payload}\n\n"

        log_event("analysis_started", analysis_id=analysis_id, repository_path=repo_path)
        yield make_sse("progress", {"step": "fetching", "message": f"Cloning & scanning repository files..."})

        # 1. Fetcher & Validation
        context = RepositoryFetcher.fetch_repository(repo_path)
        if context.error:
            log_event("fetcher_failed", level="error", analysis_id=analysis_id, error=context.error)
            yield make_sse("error", {"detail": context.error})
            return

        yield make_sse("progress", {
            "step": "parsed_context",
            "message": f"Repository scanned: {context.total_files} files, {context.total_lines} lines of code ({context.primary_language.value})."
        })

        # 2. Parser & AST Graph
        yield make_sse("progress", {"step": "parsing", "message": "Building Tree-sitter AST & import dependency graph..."})
        parser_service = TreeSitterParserService(context)
        parsed_repo = parser_service.parse()

        # 3. Static Tool Runner (Ruff, Bandit, ESLint, pip-audit)
        yield make_sse("progress", {"step": "static_analysis", "message": "Running static diagnostics (Ruff, Bandit, pip-audit)..."})
        bundle = AnalysisRunnerService.create_bundle(context, parsed_repo)

        domain_findings = {}

        # 4. Announce all 5 domain agents starting simultaneously, then run in parallel
        for domain_key, msg in [
            ("architecture", "Auditing module boundaries & circular imports..."),
            ("code_quality", "Auditing linter diagnostics & code quality... [OpenRouter]"),
            ("security", "Auditing security vulnerabilities & risk posture..."),
            ("documentation", "Evaluating README & docstrings coverage... [OpenRouter]"),
            ("dependency", "Auditing third-party package dependencies... [OpenRouter]"),
        ]:
            yield make_sse("domain_start", {"domain": domain_key, "message": msg})

        # Fire all 5 agents in parallel — Gemini handles arch/security, OpenRouter handles quality/docs/deps
        arch_res, quality_res, sec_res, doc_res, dep_res = await asyncio.gather(
            LLMAgentService.run_architecture_agent(bundle),
            LLMAgentService.run_code_quality_agent(bundle),
            LLMAgentService.run_security_agent(bundle),
            LLMAgentService.run_documentation_agent(bundle),
            LLMAgentService.run_dependency_agent(bundle),
        )

        for domain_key, finding in [
            ("architecture", arch_res),
            ("code_quality", quality_res),
            ("security", sec_res),
            ("documentation", doc_res),
            ("dependency", dep_res),
        ]:
            domain_findings[domain_key] = finding
            yield make_sse("domain_result", {"domain": domain_key, "finding": finding.model_dump()})

        # Overview agent runs after all domain agents (needs their output to synthesize)
        yield make_sse("domain_start", {"domain": "overview", "message": "Synthesizing master executive summary..."})
        overview_res = await LLMAgentService.run_overview_agent(bundle, domain_findings)
        domain_findings["overview"] = overview_res
        yield make_sse("domain_result", {"domain": "overview", "finding": overview_res.model_dump()})

        # Final Report Consolidation
        total_latency = round(time.time() - start_time, 4)
        completed_at = datetime.now(timezone.utc).isoformat()
        valid_scores = [f.score for f in domain_findings.values() if f.score is not None]
        overall_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 8

        if overall_score >= 9:
            grade = "A"
        elif overall_score >= 8:
            grade = "B"
        elif overall_score >= 7:
            grade = "C"
        elif overall_score >= 6:
            grade = "D"
        else:
            grade = "F"

        report = EngineeringReport(
            analysis_id=analysis_id,
            status="success",
            total_latency_seconds=total_latency,
            overall_score=overall_score,
            overall_grade=grade,
            executive_summary=overview_res.summary,
            repository_path=context.repository_path,
            primary_language=context.primary_language.value,
            total_files=context.total_files,
            total_lines=context.total_lines,
            domain_findings=domain_findings
        )

        await save_analysis_record(
            analysis_id=analysis_id,
            repo_path=context.repository_path,
            status="success",
            created_at=created_at,
            completed_at=completed_at,
            latency_seconds=total_latency,
            report_dict=report.model_dump()
        )

        log_event(
            "analysis_completed",
            analysis_id=analysis_id,
            total_latency_seconds=total_latency,
            overall_score=overall_score,
            overall_grade=grade
        )

        yield make_sse("complete", report.model_dump())

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get(
    f"{settings.API_V1_STR}/history",
    status_code=status.HTTP_200_OK,
    summary="Retrieve list of recent repository analyses from SQLite database"
)
async def get_history(limit: int = 10):
    """Fetch recent analysis records metadata from SQLite."""
    from src.backend.db import get_recent_analyses
    return await get_recent_analyses(limit)


@app.get(
    f"{settings.API_V1_STR}/analysis/{{analysis_id}}",
    response_model=EngineeringReport,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a past analysis report by analysis_id from SQLite database"
)
async def get_analysis_by_id(analysis_id: str) -> EngineeringReport:
    """Fetch report payload from SQLite by analysis_id."""
    report_data = await get_analysis_report(analysis_id)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis report '{analysis_id}' not found in database."
        )
    return EngineeringReport(**report_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)
