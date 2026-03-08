"""
Repository Analyzer - Detects tech stack, calculates health score, and generates suggestions.
"""

from typing import Optional


# Common known packages/frameworks for tech stack hints
PYTHON_PACKAGES = {
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "requests": "Requests",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "pytest": "pytest",
    "sqlalchemy": "SQLAlchemy",
}
JS_PACKAGES = {
    "react": "React",
    "vue": "Vue",
    "express": "Express",
    "next": "Next.js",
    "typescript": "TypeScript",
    "jest": "Jest",
}


def detect_tech_stack(
    repo_language: str,
    file_paths: list[str],
    requirements_content: Optional[str] = None,
    package_json_content: Optional[str] = None,
) -> list[str]:
    """
    Detect tech stack from repository language, file structure, and manifest files.

    Returns:
        List of detected technologies (e.g. ["Python", "Flask", "pytest"])
    """
    tech_stack = set()

    # Primary language from GitHub
    if repo_language and repo_language != "Unknown":
        tech_stack.add(repo_language)

    # From file extensions
    for path in file_paths:
        lower = path.lower()
        if lower.endswith(".py"):
            tech_stack.add("Python")
        elif lower.endswith(".js") or lower.endswith(".jsx"):
            tech_stack.add("JavaScript")
        elif lower.endswith(".ts") or lower.endswith(".tsx"):
            tech_stack.add("TypeScript")
        elif lower.endswith(".html"):
            tech_stack.add("HTML")
        elif lower.endswith(".css"):
            tech_stack.add("CSS")
        elif lower.endswith(".go"):
            tech_stack.add("Go")
        elif lower.endswith(".rs"):
            tech_stack.add("Rust")
        elif lower.endswith(".java"):
            tech_stack.add("Java")

    # From requirements.txt
    if requirements_content:
        tech_stack.add("Python")
        for line in requirements_content.splitlines():
            line = line.strip().lower()
            if line.startswith("#") or not line:
                continue
            # Extract package name (before == or [)
            pkg = line.split("==")[0].split("[")[0].split(">=")[0].strip()
            if pkg in PYTHON_PACKAGES:
                tech_stack.add(PYTHON_PACKAGES[pkg])

    # From package.json (simple regex for common deps)
    if package_json_content:
        tech_stack.add("JavaScript")
        lower = package_json_content.lower()
        for pkg, label in JS_PACKAGES.items():
            if f'"{pkg}"' in lower or f"'{pkg}'" in lower:
                tech_stack.add(label)

    return sorted(tech_stack)


def calculate_health_score(
    has_readme: bool,
    has_license: bool,
    has_tests: bool,
    has_ci_cd: bool,
) -> tuple[int, list[str]]:
    """
    Calculate repository health score out of 100.

    Each criterion: 25 points.
    Returns: (score, suggestions for missing items)
    """
    score = 0
    suggestions = []

    if has_readme:
        score += 25
    else:
        suggestions.append("Add README with project description and setup instructions.")

    if has_license:
        score += 25
    else:
        suggestions.append("Add a LICENSE file (e.g. MIT, Apache 2.0).")

    if has_tests:
        score += 25
    else:
        suggestions.append("Add automated tests (e.g. pytest for Python, Jest for JS).")

    if has_ci_cd:
        score += 25
    else:
        suggestions.append("Add CI/CD workflow (e.g. GitHub Actions).")

    return score, suggestions


def check_repo_health(file_paths: list[str], repo_info: dict) -> dict:
    """
    Check repository health based on file structure.

    Returns:
        {
            "score": int,
            "suggestions": list[str],
            "has_readme": bool,
            "has_license": bool,
            "has_tests": bool,
            "has_ci_cd": bool,
        }
    """
    paths_lower = [p.lower() for p in file_paths]

    # Check for README (any common format)
    has_readme = any(
        p == "readme.md"
        or p == "readme.rst"
        or p == "readme.txt"
        or p.endswith("/readme.md")
        for p in paths_lower
    )

    # Check for LICENSE
    has_license = any(
        p == "license" or p == "license.txt" or "license" in p
        for p in paths_lower
    )

    # Check for tests folder or test files
    has_tests = (
        any("test" in p or "tests" in p or "_test" in p for p in paths_lower)
        or any(p.startswith("test_") or p.endswith("_test.py") for p in paths_lower)
    )

    # Check for CI/CD (GitHub Actions, etc.)
    has_ci_cd = any(
        ".github/workflows" in p
        or ".github/actions" in p
        or ".travis" in p
        or "jenkinsfile" in p
        for p in paths_lower
    )

    score, suggestions = calculate_health_score(
        has_readme, has_license, has_tests, has_ci_cd
    )

    return {
        "score": score,
        "suggestions": suggestions,
        "has_readme": has_readme,
        "has_license": has_license,
        "has_tests": has_tests,
        "has_ci_cd": has_ci_cd,
    }
