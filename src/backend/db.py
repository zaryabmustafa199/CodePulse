"""
SQLite Database Layer for CodePulse Backend.
Provides schema initialization and thread-safe, non-blocking I/O functions
wrapped via asyncio.to_thread for persisting analyses and reports.
"""

import sqlite3
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "codepulse.db"


def get_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database with WAL mode and busy timeout for multi-worker concurrency."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the SQLite database schema if tables do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                repository_path TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                latency_seconds REAL,
                error_message TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                analysis_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
            );
        """)
        conn.commit()


def _save_analysis_record_sync(
    analysis_id: str,
    repo_path: str,
    status: str,
    created_at: str,
    completed_at: str,
    latency_seconds: float,
    report_dict: Dict[str, Any]
) -> None:
    """Synchronous worker function to save analysis and report to SQLite."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO analyses (id, repository_path, status, created_at, completed_at, latency_seconds)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (analysis_id, repo_path, status, created_at, completed_at, latency_seconds))
        
        cursor.execute("""
            INSERT OR REPLACE INTO reports (analysis_id, report_json)
            VALUES (?, ?);
        """, (analysis_id, json.dumps(report_dict)))
        conn.commit()


def _get_analysis_report_sync(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Synchronous worker function to fetch report by analysis_id from SQLite."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT report_json FROM reports WHERE analysis_id = ?;
        """, (analysis_id,))
        row = cursor.fetchone()
        if row and row["report_json"]:
            return json.loads(row["report_json"])
        return None


async def save_analysis_record(
    analysis_id: str,
    repo_path: str,
    status: str,
    created_at: str,
    completed_at: str,
    latency_seconds: float,
    report_dict: Dict[str, Any]
) -> None:
    """Non-blocking async wrapper to save analysis record and report to SQLite."""
    await asyncio.to_thread(
        _save_analysis_record_sync,
        analysis_id,
        repo_path,
        status,
        created_at,
        completed_at,
        latency_seconds,
        report_dict
    )


async def get_analysis_report(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Non-blocking async wrapper to fetch analysis report from SQLite."""
    return await asyncio.to_thread(_get_analysis_report_sync, analysis_id)


def _get_recent_analyses_sync(limit: int = 10) -> list[Dict[str, Any]]:
    """Synchronous worker function to fetch recent analysis metadata from SQLite."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, repository_path, status, created_at, completed_at, latency_seconds
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


async def get_recent_analyses(limit: int = 10) -> list[Dict[str, Any]]:
    """Non-blocking async wrapper to fetch recent analysis history from SQLite."""
    return await asyncio.to_thread(_get_recent_analyses_sync, limit)
