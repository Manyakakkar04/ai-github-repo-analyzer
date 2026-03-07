# AI GitHub Repository Analyzer

A simple Flask app that analyzes GitHub repositories: fetches metadata, detects tech stack, calculates a health score, and provides per-file code suggestions.

## Setup

```bash
cd ai-github-repo-analyzer
pip install -r requirements.txt
```

Optional: Copy `.env.example` to `.env` and add your `GITHUB_TOKEN` for higher API rate limits (5000/hr vs 60/hr unauthenticated).

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser. Enter a GitHub repo URL (e.g. `https://github.com/pallets/flask`) and click Analyze.
