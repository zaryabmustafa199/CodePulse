"""
CodePulse Main FastAPI Application.
Exposes synchronous HTTP API endpoint POST /api/v1/analyze per INTERFACES.md specifications.
"""

import time
from pathlib import Path
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

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CodePulse Engineering Intelligence Platform Backend API"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    Execute full vertical slice pipeline synchronously:
    Fetcher -> Tree-sitter Parser -> Analysis Runner (Ruff) -> LLM Overview Agent -> EngineeringReport.
    """
    start_time = time.time()
    repo_path = request.repository_path.strip()

    # 1. Fetcher & Validation
    context = RepositoryFetcher.fetch_repository(repo_path)
    if context.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=context.error
        )

    # 2. Parser & AST Graph
    parser_service = TreeSitterParserService(context)
    parsed_repo = parser_service.parse()

    # 3. Analysis Runner (Ruff)
    bundle = AnalysisRunnerService.create_bundle(context, parsed_repo)

    # 4. LLM Overview & Security Agent Calls
    overview_finding = LLMAgentService.run_overview_agent(bundle)
    security_finding = LLMAgentService.run_security_agent(bundle)

    # 5. Report Consolidation
    total_latency = round(time.time() - start_time, 4)
    
    # Calculate average score across Overview and Security agents
    scores = []
    if overview_finding.score is not None:
        scores.append(overview_finding.score)
    if security_finding.score is not None:
        scores.append(security_finding.score)
        
    overall_score = round(sum(scores) / len(scores)) if scores else 8
    
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
        status="success",
        total_latency_seconds=total_latency,
        overall_score=overall_score,
        overall_grade=grade,
        executive_summary=overview_finding.summary,
        repository_path=context.repository_path,
        primary_language=context.primary_language.value,
        total_files=context.total_files,
        total_lines=context.total_lines,
        domain_findings={
            AgentDomain.OVERVIEW.value: overview_finding,
            AgentDomain.SECURITY.value: security_finding
        }
    )

    return report


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)
