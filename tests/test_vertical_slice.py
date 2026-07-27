"""
Automated Integration Tests for CodePulse Week 1 Vertical Slice.
Tests API root health check, repository fetching, AST parsing, and POST /api/v1/analyze.
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
    """Verify POST /api/v1/analyze against local repository."""
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
    assert "overview" in data["domain_findings"]
    
    overview = data["domain_findings"]["overview"]
    assert overview["domain"] == "overview"
    assert len(overview["summary"]) > 0


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
    """Verify JS/TS repository detection and parsing."""
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
    assert "security" in data["domain_findings"]

