"""
Code Analyzer - Performs static analysis on individual files and generates explanations.
"""

import re
from typing import Optional


# Line count threshold for "very large file" warning
LARGE_FILE_LINES = 300

# Patterns for potential hardcoded secrets
SECRET_PATTERNS = [
    r"API_KEY\s*=\s*['\"][^'\"]+['\"]",
    r"SECRET\s*=\s*['\"][^'\"]+['\"]",
    r"password\s*=\s*['\"][^'\"]+['\"]",
    r"api_key\s*=\s*['\"][^'\"]+['\"]",
    r"secret_key\s*=\s*['\"][^'\"]+['\"]",
    r"token\s*=\s*['\"][^'\"]+['\"]",
]

# Debug print patterns (Python)
DEBUG_PRINT_PATTERNS = [
    r"\bprint\s*\(",
    r"\bconsole\.log\s*\(",
    r"\bconsole\.debug\s*\(",
]

# API call patterns without obvious try/except
API_PATTERNS = [
    r"requests\.get\s*\(",
    r"requests\.post\s*\(",
    r"fetch\s*\(",
    r"axios\.(get|post|put|delete)\s*\(",
]


def analyze_file(content: str, path: str, language: str = "") -> dict:
    """
    Perform static analysis on file content.

    Returns:
        {
            "debug_prints": list of {line_num, line},
            "possible_secrets": list of {line_num, match},
            "api_without_try": list of {line_num, line},
            "is_large": bool,
            "line_count": int,
            "explanation": list[str],
            "suggestions": list[str],
        }
    """
    lines = content.splitlines()
    line_count = len(lines)
    is_large = line_count > LARGE_FILE_LINES

    debug_prints = []
    possible_secrets = []
    api_without_try = []

    for i, line in enumerate(lines, start=1):
        # Skip empty and comment lines for some checks
        stripped = line.strip()

        # Debug print statements
        for pattern in DEBUG_PRINT_PATTERNS:
            if re.search(pattern, line):
                debug_prints.append({"line_num": i, "line": line.strip()[:80]})
                break

        # Possible hardcoded secrets
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                possible_secrets.append({"line_num": i, "match": line.strip()[:80]})
                break

        # API calls - simple heuristic: no try/except in recent lines
        for pattern in API_PATTERNS:
            if re.search(pattern, line):
                # Check if there's a try block in the last 10 lines
                context = "\n".join(lines[max(0, i - 15) : i])
                if "try" not in context and "catch" not in context:
                    api_without_try.append({"line_num": i, "line": line.strip()[:80]})
                break

    # Build explanation from static analysis
    explanation = extract_file_explanation(content, path, lines)
    suggestions = build_suggestions(
        debug_prints, possible_secrets, api_without_try, is_large
    )

    return {
        "debug_prints": debug_prints,
        "possible_secrets": possible_secrets,
        "api_without_try": api_without_try,
        "is_large": is_large,
        "line_count": line_count,
        "explanation": explanation,
        "suggestions": suggestions,
    }


def extract_file_explanation(content: str, path: str, lines: list[str]) -> list[str]:
    """
    Extract a simple explanation of the file: functions, classes, Flask routes, DB usage.
    """
    explanation = []

    # Python: def, class
    if path.endswith(".py"):
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r"^def\s+(\w+)\s*\(", stripped):
                m = re.search(r"def\s+(\w+)\s*\([^)]*\)", stripped)
                if m:
                    name = m.group(1)
                    if name.startswith("_"):
                        continue
                    doc = get_next_docstring(lines, i)
                    explanation.append(f"Function: {name}() - {doc or 'no docstring'}")
            elif re.match(r"^class\s+(\w+)\s*", stripped):
                m = re.search(r"class\s+(\w+)\s*", stripped)
                if m:
                    explanation.append(f"Class: {m.group(1)}")
            elif "@app.route" in stripped or "@.route" in stripped:
                m = re.search(r'["\']([^"\']+)["\']', stripped)
                path_val = m.group(1) if m else "?"
                explanation.append(f"Flask route: {path_val}")
            elif "Session" in line or "session" in line or "db." in line or "create_engine" in line:
                if not any("database" in e.lower() for e in explanation):
                    explanation.append("Database usage detected")

    # JavaScript/TypeScript
    elif path.endswith((".js", ".ts", ".jsx", ".tsx")):
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r"^(export\s+)?(async\s+)?function\s+(\w+)\s*\(", stripped):
                m = re.search(r"function\s+(\w+)\s*\(", stripped)
                if m:
                    explanation.append(f"Function: {m.group(1)}()")
            elif re.match(r"^export\s+default\s+function", stripped):
                explanation.append("Default export function")
            elif re.match(r"^class\s+(\w+)\s*", stripped):
                m = re.search(r"class\s+(\w+)\s*", stripped)
                if m:
                    explanation.append(f"Class: {m.group(1)}")
            elif "app.get" in stripped or "app.post" in stripped or "router." in stripped:
                m = re.search(r'["\']([^"\']+)["\']', stripped)
                path_val = m.group(1) if m else "?"
                explanation.append(f"Route: {path_val}")

    # Fallback
    if not explanation:
        explanation.append(f"Code file: {path.split('/')[-1]}")

    return explanation


def get_next_docstring(lines: list[str], after_line: int) -> Optional[str]:
    """Get first docstring after the given line (for Python)."""
    for i in range(after_line, min(after_line + 5, len(lines))):
        line = lines[i].strip()
        if '"""' in line or "'''" in line:
            # Extract first line of docstring
            doc = line.replace('"""', "").replace("'''", "").strip()
            if doc:
                return doc[:80]
        elif line and not line.startswith("#"):
            break
    return None


def build_suggestions(
    debug_prints: list,
    possible_secrets: list,
    api_without_try: list,
    is_large: bool,
) -> list[str]:
    """Build improvement suggestions from analysis results."""
    suggestions = []
    if debug_prints:
        suggestions.append(
            f"Remove or replace {len(debug_prints)} debug print/console.log statements before production."
        )
    if possible_secrets:
        suggestions.append(
            "Possible hardcoded secrets detected. Use environment variables (e.g. os.environ) instead."
        )
    if api_without_try:
        suggestions.append(
            "API calls without exception handling. Wrap in try/except (Python) or try/catch (JS)."
        )
    if is_large:
        suggestions.append(
            f"File has more than {LARGE_FILE_LINES} lines. Consider splitting into smaller modules."
        )
    if not suggestions:
        suggestions.append("No major issues detected. Keep up the good work!")
    return suggestions
