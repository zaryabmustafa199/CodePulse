"""
Repository Fetcher Service for CodePulse.
Validates workspace paths, filters excluded paths, checks line/file limits,
and extracts baseline metadata into RepositoryContext.
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional
from src.backend.config import settings
from src.backend.models.schemas import RepositoryContext, Language, Framework


class RepositoryFetcher:
    """Service to fetch, validate, and inventory repositories."""

    @staticmethod
    def is_excluded(path: Path) -> bool:
        """Check if path contains an excluded directory or extension."""
        parts = path.parts
        for excluded in settings.EXCLUDED_PATHS:
            if excluded in parts:
                return True
        name = path.name
        for ext in settings.EXCLUDED_EXTENSIONS:
            if name.endswith(ext):
                return True
        return False

    @classmethod
    def fetch_repository(cls, repo_path_str: str) -> RepositoryContext:
        """
        Validate and inventory a repository at repo_path_str.
        Returns RepositoryContext with metadata or error.
        """
        # Check if input is a remote Git/GitHub URL
        is_remote_url = repo_path_str.startswith(("http://", "https://", "git@")) or "github.com" in repo_path_str
        temp_dir_obj: Optional[tempfile.TemporaryDirectory] = None

        if is_remote_url:
            try:
                # Ensure URL is clean
                clean_url = repo_path_str.strip()
                temp_dir_obj = tempfile.TemporaryDirectory(prefix="codepulse_git_")
                target_dir = Path(temp_dir_obj.name)

                # Clone shallowly with 60s timeout
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", clean_url, str(target_dir)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False
                )

                if result.returncode != 0:
                    err_msg = result.stderr.strip() or "Failed to clone remote git repository."
                    return RepositoryContext(
                        repository_path=repo_path_str,
                        error=f"Git clone error: {err_msg}"
                    )

                repo_path = target_dir

            except subprocess.TimeoutExpired:
                return RepositoryContext(
                    repository_path=repo_path_str,
                    error="Git clone timed out after 60 seconds."
                )
            except Exception as e:
                return RepositoryContext(
                    repository_path=repo_path_str,
                    error=f"Failed to clone repository URL: {str(e)}"
                )
        else:
            repo_path = Path(repo_path_str).resolve()

            # Prevent root path mapping (e.g., D:\ or C:\)
            if len(repo_path.parts) <= 1:
                return RepositoryContext(
                    repository_path=repo_path_str,
                    error="Repository path cannot be the root partition."
                )

            if not repo_path.exists() or not repo_path.is_dir():
                return RepositoryContext(
                    repository_path=repo_path_str,
                    error=f"Repository path does not exist or is not a directory: {repo_path_str}"
                )

        file_manifest: List[str] = []
        total_lines = 0
        python_files = 0
        jsts_files = 0

        readme_content: Optional[str] = None
        dependency_raw: Optional[str] = None

        for root, dirs, files in os.walk(repo_path):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in settings.EXCLUDED_PATHS]

            for file_name in files:
                full_path = Path(root) / file_name
                if cls.is_excluded(full_path):
                    continue

                rel_path = full_path.relative_to(repo_path).as_posix()

                # Read README if encountered
                if file_name.lower() in ("readme.md", "readme.txt") and not readme_content:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            readme_content = f.read(2000)  # First 2000 chars
                    except Exception:
                        pass

                # Read dependency manifest
                if file_name in ("requirements.txt", "package.json", "pyproject.toml") and not dependency_raw:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            dependency_raw = f.read(2000)
                    except Exception:
                        pass

                ext = full_path.suffix.lower()
                if ext in (".py", ".js", ".jsx", ".ts", ".tsx"):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = len(f.readlines())

                        if line_count > settings.MAX_SINGLE_FILE_LINES:
                            continue  # Skip bundled / giant generated files

                        file_manifest.append(rel_path)
                        total_lines += line_count

                        if ext == ".py":
                            python_files += 1
                        else:
                            jsts_files += 1

                    except Exception:
                        pass

        # Validation assertions
        if len(file_manifest) == 0:
            return RepositoryContext(
                repository_path=str(repo_path),
                error="No valid Python or TypeScript/JavaScript source files found."
            )

        if len(file_manifest) > settings.MAX_FILES_LIMIT:
            return RepositoryContext(
                repository_path=str(repo_path),
                error=f"Repository exceeds maximum file count limit ({len(file_manifest)} > {settings.MAX_FILES_LIMIT})."
            )

        if total_lines > settings.MAX_LOC_LIMIT:
            return RepositoryContext(
                repository_path=str(repo_path),
                error=f"Repository exceeds maximum lines of code limit ({total_lines} > {settings.MAX_LOC_LIMIT})."
            )

        primary_lang = Language.PYTHON if python_files >= jsts_files else Language.TYPESCRIPT

        # Framework heuristics
        framework = Framework.UNKNOWN
        manifest_str = " ".join(file_manifest).lower()
        if "fastapi" in manifest_str or (dependency_raw and "fastapi" in dependency_raw.lower()):
            framework = Framework.FASTAPI
        elif "react" in manifest_str or (dependency_raw and "react" in dependency_raw.lower()):
            framework = Framework.REACT
        elif "django" in manifest_str or (dependency_raw and "django" in dependency_raw.lower()):
            framework = Framework.DJANGO

        context = RepositoryContext(
            repository_path=repo_path_str if is_remote_url else str(repo_path),
            primary_language=primary_lang,
            framework=framework,
            total_files=len(file_manifest),
            total_lines=total_lines,
            file_manifest=file_manifest,
            readme_content=readme_content,
            dependency_file_raw=dependency_raw
        )

        # Cleanup temp directory if remote clone
        if temp_dir_obj:
            try:
                temp_dir_obj.cleanup()
            except Exception:
                pass

        return context
