"""
AI GitHub Repository Analyzer - Flask application entry point.
"""

from flask import Flask, render_template, request, jsonify
import requests

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
    return render_template("index.html")


# ================= REPOSITORY ANALYZER =================

@app.route("/analyze", methods=["POST"])
def analyze_repo():

    data = request.get_json() or request.form
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Please enter a GitHub repository URL."}), 400

    owner, repo = parse_github_url(url)

    if not owner or not repo:
        return jsonify({"error": "Invalid GitHub URL"}), 400

    try:

        repo_info = get_repo_info(owner, repo)
        branch = repo_info.get("default_branch", "main")

        code_files = get_file_tree(owner, repo, branch)
        file_paths = [f["path"] for f in code_files]

        all_paths = get_all_tree_paths(owner, repo, branch)

        health = check_repo_health(all_paths, repo_info)

        requirements_content = None
        package_json_content = None

        try:
            req_path = next(
                (p for p in all_paths if "requirements" in p.lower() and p.endswith(".txt")),
                None,
            )
            if req_path:
                requirements_content = get_file_content(owner, repo, req_path, branch)
        except GitHubAPIError:
            pass

        try:
            if "package.json" in all_paths:
                package_json_content = get_file_content(owner, repo, "package.json", branch)
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
        })

    except GitHubAPIError as e:
        return jsonify({"success": False, "error": e.message}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ================= FILE ANALYZER =================

@app.route("/analyze-file", methods=["POST"])
def analyze_file_route():

    data = request.get_json() or request.form

    owner = data.get("owner")
    repo = data.get("repo")
    path = data.get("path")
    branch = data.get("branch", "main")

    if not owner or not repo or not path:
        return jsonify({"error": "Missing parameters"}), 400

    try:

        content = get_file_content(owner, repo, path, branch)

        ext = path.split(".")[-1] if "." in path else ""

        analysis = analyze_file(content, path, ext)

        return jsonify(analysis)

    except GitHubAPIError as e:
        return jsonify({"error": e.message}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= PR ANALYZER =================

@app.route("/analyze-pr", methods=["POST"])
def analyze_pr():

    data = request.get_json()

    pr_url = data.get("pr_url")

    if not pr_url:
        return jsonify({"error": "PR URL required"}), 400

    try:

        parts = pr_url.split("/")

        owner = parts[3]
        repo = parts[4]
        pr_number = parts[6]

        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

        response = requests.get(api_url)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch PR"}), 400

        files = response.json()

        result = []

        for f in files:

            result.append({
                "filename": f["filename"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "changes": f["changes"]
            })

        return jsonify({
            "success": True,
            "files_changed": len(files),
            "files": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)