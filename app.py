"""
AI GitHub Repository Analyzer - Flask application entry point.
"""

from flask import Flask, render_template, request, jsonify
from github_client import (
    parse_github_url,
    get_repo_info,
    get_file_tree,
    get_file_content,
    get_all_tree_paths,
    GitHubAPIError,
)
from repo_analyzer import detect_tech_stack, check_repo_health
from code_analyzer import analyze_file

app = Flask(__name__)


@app.route("/")
def index():
    """Render home page with URL input form."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_repo():
    """
    Analyze a GitHub repository.
    Expects JSON: { "url": "https://github.com/owner/repo" }

    Returns JSON with:
    - repo_info, tech_stack, health, file_list, error
    """
    data = request.get_json() or request.form
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Please enter a GitHub repository URL."}), 400

    owner, repo = parse_github_url(url)
    if not owner or not repo:
        return jsonify(
            {"error": "Invalid GitHub URL. Example: https://github.com/pallets/flask"}
        ), 400

    try:
        # Fetch repository metadata
        repo_info = get_repo_info(owner, repo)
        branch = repo_info.get("default_branch", "main")

        # Fetch file tree (code files only, limit 50)
        code_files = get_file_tree(owner, repo, branch)
        file_paths = [f["path"] for f in code_files]

        # Fetch full tree for health check
        all_paths = get_all_tree_paths(owner, repo, branch)
        health = check_repo_health(all_paths, repo_info)

        # Detect tech stack - fetch manifest files if present
        requirements_content = None
        package_json_content = None
        try:
            req_path = next(
                (
                    p
                    for p in all_paths
                    if "requirements" in p.lower() and p.endswith(".txt")
                ),
                None,
            )
            if req_path:
                requirements_content = get_file_content(
                    owner, repo, req_path, branch
                )
        except GitHubAPIError:
            pass
        try:
            if "package.json" in all_paths:
                package_json_content = get_file_content(
                    owner, repo, "package.json", branch
                )
        except GitHubAPIError:
            pass

        tech_stack = detect_tech_stack(
            repo_info.get("language", ""),
            file_paths,
            requirements_content,
            package_json_content,
        )

        return jsonify({
            "success": True,
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "repo_info": repo_info,
            "tech_stack": tech_stack,
            "health": health,
            "file_list": [{"path": f["path"]} for f in code_files],
            "error": None,
        })

    except GitHubAPIError as e:
        return jsonify({"success": False, "error": e.message}), (
            404 if e.status_code == 404 else 502
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/analyze-file", methods=["POST"])
def analyze_file_route():
    """
    Analyze a single file from a repository.
    Expects JSON: { "owner": "", "repo": "", "path": "", "branch": "main" }

    Returns JSON: { "explanation": [], "suggestions": [], ... }
    """
    data = request.get_json() or request.form
    owner = (data.get("owner") or "").strip()
    repo = (data.get("repo") or "").strip()
    path = (data.get("path") or "").strip()
    branch = (data.get("branch") or "main").strip()

    if not owner or not repo or not path:
        return jsonify({"error": "Missing owner, repo, or path."}), 400

    try:
        content = get_file_content(owner, repo, path, branch)
        ext = path.split(".")[-1].lower() if "." in path else ""
        analysis = analyze_file(content, path, ext)

        return jsonify({
            "success": True,
            "explanation": analysis["explanation"],
            "suggestions": analysis["suggestions"],
            "debug_prints": analysis["debug_prints"],
            "possible_secrets": analysis["possible_secrets"],
            "api_without_try": analysis["api_without_try"],
            "is_large": analysis["is_large"],
            "line_count": analysis["line_count"],
        })

    except GitHubAPIError as e:
        return jsonify({"success": False, "error": e.message}), (
            404 if e.status_code == 404 else 502
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
