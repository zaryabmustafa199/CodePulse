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
