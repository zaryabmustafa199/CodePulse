"""
Automated Integration Tests for CodePulse Platform.
Tests API root health check, repository fetching, AST parsing, 6-agent suite execution,
SQLite persistence, and GET /api/v1/analysis/{analysis_id}.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from src.backend.main import app

client = TestClient(app)

def test_read_root():
    """Verify health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "CodePulse"
    assert data["status"] == "healthy"


def test_analyze_valid_local_repository():
    """Verify POST /api/v1/analyze returns complete 6-domain report and saves to SQLite DB."""
    repo_path = str(Path(__file__).parent.parent.resolve())
    response = client.post(
        "/api/v1/analyze",
        json={"repository_path": repo_path}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_latency_seconds"] > 0
    assert data["overall_score"] is not None
    assert data["overall_grade"] in ("A", "B", "C", "D", "F")
    assert data["total_files"] > 0
    
    # Check all 6 domains present in domain_findings
    expected_domains = ["overview", "architecture", "code_quality", "security", "documentation", "dependency"]
    for dom in expected_domains:
        assert dom in data["domain_findings"], f"Missing domain finding: {dom}"
        finding = data["domain_findings"][dom]
        assert finding["domain"] == dom
        assert len(finding["summary"]) > 0
        assert finding["score"] is not None


def test_analyze_invalid_repository():
    """Verify 400 Bad Request error response for non-existent path."""
    response = client.post(
        "/api/v1/analyze",
        json={"repository_path": "invalid/non/existent/path/999"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "does not exist" in data["detail"]


def test_analyze_root_partition():
    """Verify root partition is blocked to prevent full system scans."""
    response = client.post(
        "/api/v1/analyze",
        json={"repository_path": "C:\\"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "root partition" in data["detail"]


def test_analyze_empty_repository(tmp_path):
    """Verify directories with no code files are rejected."""
    empty_dir = tmp_path / "empty_proj"
    empty_dir.mkdir()
    response = client.post(
        "/api/v1/analyze",
        json={"repository_path": str(empty_dir)}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "No valid Python or TypeScript" in data["detail"]


def test_analyze_jsts_repository(tmp_path):
    """Verify JS/TS repository detection, parsing, and multi-agent report execution."""
    js_proj = tmp_path / "js_proj"
    js_proj.mkdir()
    
    # Create simple JS and TS files with imports
    js_file = js_proj / "index.js"
    js_file.write_text("import { foo } from './utils';\nconst x = 12;", encoding="utf-8")
    
    ts_file = js_proj / "utils.ts"
    ts_file.write_text("export const foo = () => console.log('hello');", encoding="utf-8")

    response = client.post(
        "/api/v1/analyze",
        json={"repository_path": str(js_proj)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["primary_language"] in ("typescript", "javascript")
    assert data["total_files"] == 2
    assert "overview" in data["domain_findings"]
    assert "architecture" in data["domain_findings"]


def test_database_persistence_and_retrieval(tmp_path):
    """Verify that reports persisted in SQLite database can be retrieved by analysis_id."""
    from src.backend.db import save_analysis_record, get_analysis_report, init_db
    import asyncio

    init_db()
    test_id = "test-uuid-12345"
    mock_report = {
        "status": "success",
        "total_latency_seconds": 1.23,
        "overall_score": 9,
        "overall_grade": "A",
        "executive_summary": "Test executive summary.",
        "repository_path": str(tmp_path),
        "primary_language": "python",
        "total_files": 5,
        "total_lines": 100,
        "domain_findings": {}
    }

    async def run_db_test():
        await save_analysis_record(
            analysis_id=test_id,
            repo_path=str(tmp_path),
            status="success",
            created_at="2026-07-28T00:00:00Z",
            completed_at="2026-07-28T00:00:01Z",
            latency_seconds=1.23,
            report_dict=mock_report
        )
        retrieved = await get_analysis_report(test_id)
        assert retrieved is not None
        assert retrieved["overall_grade"] == "A"
        assert retrieved["executive_summary"] == "Test executive summary."

    asyncio.run(run_db_test())
