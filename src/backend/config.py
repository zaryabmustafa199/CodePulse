"""
Configuration settings for CodePulse Backend.
Loads environment variables, default model identifiers, and validation limits.
"""

import os
from pathlib import Path

def _load_dotenv_file():
    """Lightweight auto-loader for .env variables without external dependencies."""
    env_file = Path(".env").resolve()
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val

_load_dotenv_file()


class Settings:
    PROJECT_NAME: str = "CodePulse"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Validation Limits (as per INTERFACES.md)
    MAX_LOC_LIMIT: int = 15000
    MAX_FILES_LIMIT: int = 500
    MAX_SINGLE_FILE_LINES: int = 2000

    # LLM Settings — Gemini (Primary: Architecture, Security, Overview, Dependency)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash").strip()

    # LLM Settings — OpenRouter (Secondary: Code Quality, Documentation, Dependency — independent quota pool)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    # Primary free model — verified working as of 2026-08-05
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free").strip()
    # Fallback free model if primary is unavailable
    OPENROUTER_FALLBACK_MODEL: str = os.getenv("OPENROUTER_FALLBACK_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free").strip()
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"


    # Development Mode — raises rate limit to 100 for local dev
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    PROMPT_VERSION_OVERVIEW: str = "overview-v1"
    PROMPT_VERSION_ARCHITECTURE: str = "architecture-v1"
    PROMPT_VERSION_CODE_QUALITY: str = "code-quality-v1"
    PROMPT_VERSION_SECURITY: str = "security-v1"
    PROMPT_VERSION_DOCUMENTATION: str = "documentation-v1"
    PROMPT_VERSION_DEPENDENCY: str = "dependency-v1"

    # Excluded directory & extension patterns
    EXCLUDED_PATHS: set = {
        "node_modules", "dist", "build", ".git", "__pycache__", ".venv", "venv", ".idea", ".vscode"
    }
    EXCLUDED_EXTENSIONS: set = {
        ".min.js", ".min.css", ".lock", ".snap", ".map", "_generated.py", "_generated.ts"
    }

settings = Settings()
