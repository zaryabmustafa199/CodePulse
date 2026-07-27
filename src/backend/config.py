"""
Configuration settings for CodePulse Backend.
Loads environment variables, default model identifiers, and validation limits.
"""

import os

class Settings:
    PROJECT_NAME: str = "CodePulse"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Validation Limits (as per INTERFACES.md)
    MAX_LOC_LIMIT: int = 15000
    MAX_FILES_LIMIT: int = 500
    MAX_SINGLE_FILE_LINES: int = 2000
    
    # LLM Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    PROMPT_VERSION_OVERVIEW: str = "overview-v1"
    PROMPT_VERSION_CODE_QUALITY: str = "code-quality-v1"
    
    # Excluded directory & extension patterns
    EXCLUDED_PATHS: set = {
        "node_modules", "dist", "build", ".git", "__pycache__", ".venv", "venv", ".idea", ".vscode"
    }
    EXCLUDED_EXTENSIONS: set = {
        ".min.js", ".min.css", ".lock", ".snap", ".map", "_generated.py", "_generated.ts"
    }

settings = Settings()
