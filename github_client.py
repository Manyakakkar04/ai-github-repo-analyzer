"""
GitHub API Client - Fetches repository data using GitHub REST API.
"""

import re
import base64
import requests
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

# File extensions we consider as "code files" for analysis
CODE_EXTENSIONS = (".py", ".js", ".ts", ".tsx", ".jsx")


def parse_github_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract owner and repository name from a GitHub URL.

    Examples:
        https://github.com/pallets/flask -> ("pallets", "flask")
        https://github.com/owner/repo.git -> ("owner", "repo")
        https://github.com/owner/repo/tree/main -> ("owner", "repo")

    Returns:
        Tuple of (owner, repo) or (None, None) if invalid
    """
    if not url or not url.strip():
        return None, None

    # Match: github.com/owner/repo (with optional /tree/branch, .git, trailing slash)
    pattern = r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git|/.*)?$"
    match = re.search(pattern, url.strip(), re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None, None


def get_headers() -> dict:
    """Build request headers including optional auth token for higher rate limits."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def get_repo_info(owner: str, repo: str) -> dict:
    """
    Fetch repository metadata from GitHub API.

    Returns:
        Dict with: name, description, stars, forks, language, default_branch, etc.

    Raises:
        GitHubAPIError: If API request fails
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    response = requests.get(url, headers=get_headers(), timeout=30)

    if response.status_code == 404:
        raise GitHubAPIError("Repository not found. Please check the URL.", 404)
    if response.status_code == 403:
        raise GitHubAPIError(
            "GitHub API rate limit exceeded. Try again later or add GITHUB_TOKEN.",
            403,
        )
    if response.status_code != 200:
        raise GitHubAPIError(
            f"GitHub API error: {response.status_code}",
            response.status_code,
        )

    data = response.json()
    return {
        "name": data.get("name", ""),
        "full_name": data.get("full_name", ""),
        "description": data.get("description") or "No description",
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "language": data.get("language") or "Unknown",
        "default_branch": data.get("default_branch", "main"),
        "topics": data.get("topics", []),
    }


def get_all_tree_paths(owner: str, repo: str, branch: str) -> list[str]:
    """
    Fetch all file and directory paths in the repository (for health checks).
    Uses Git Trees API recursively.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    params = {"recursive": "1"}
    response = requests.get(url, headers=get_headers(), params=params, timeout=30)
    if response.status_code != 200:
        return []
    data = response.json()
    return [item.get("path", "") for item in data.get("tree", [])]


def get_file_tree(owner: str, repo: str, branch: str) -> list[dict]:
    """
    Fetch full file tree recursively using Git Trees API.
    Returns list of file objects with path, type, size.

    Raises:
        GitHubAPIError: If API request fails
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    params = {"recursive": "1"}
    response = requests.get(url, headers=get_headers(), params=params, timeout=30)

    if response.status_code != 200:
        if response.status_code == 404:
            raise GitHubAPIError("Branch or repository not found.", 404)
        if response.status_code == 403:
            raise GitHubAPIError("GitHub API rate limit exceeded.", 403)
        raise GitHubAPIError(f"Failed to fetch file tree: {response.status_code}")

    data = response.json()
    tree = data.get("tree", [])

    # Filter to only files (not directories) with code extensions, limit to 50
    code_files = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        if any(path.lower().endswith(ext) for ext in CODE_EXTENSIONS):
            # Skip common non-source directories
            if any(
                skip in path.lower()
                for skip in ("node_modules", "__pycache__", "venv", ".git")
            ):
                continue
            code_files.append(
                {"path": path, "size": item.get("size", 0), "sha": item.get("sha")}
            )
            if len(code_files) >= 50:
                break

    return code_files


def get_file_content(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """
    Fetch raw file content from GitHub Contents API.
    Uses raw media type to get plain text (not base64).

    Returns:
        File content as string.

    Raises:
        GitHubAPIError: If API request fails or file too large
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": branch}
    headers = get_headers()
    headers["Accept"] = "application/vnd.github.raw"

    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 404:
        raise GitHubAPIError("File not found.", 404)
    if response.status_code == 403:
        raise GitHubAPIError("GitHub API rate limit exceeded.", 403)
    if response.status_code != 200:
        raise GitHubAPIError(f"Failed to fetch file: {response.status_code}")

    # Raw response returns content directly; large files (>1MB) may fail
    content = response.text
    if len(content) > 1_000_000:
        raise GitHubAPIError("File is too large to analyze (>1MB).")

    return content
