# AI GitHub Repository Analyzer

Analyze GitHub repositories and pull requests to understand tech stack, repository health, and file-level insights.

---

## Table of Contents
- [Overview](#overview)  
- [Features](#features)  
- [Demo](#demo)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Project Structure](#project-structure)  
- [Future Improvements](#future-improvements)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Overview
The **AI GitHub Repository Analyzer** is a Flask-based application that allows users to:  

- Analyze a GitHub repository to get insights on its tech stack, health score, and file-level issues.  
- Analyze pull requests to see which files were changed, along with additions, deletions, and total changes.  
- Provide actionable suggestions at the file level (e.g., missing docstrings, debug prints, large files, database usage).  

This project helps developers quickly understand repositories and pull requests before contributing or reviewing code.

---

## Features

### Repository Analysis
- Fetches repository metadata via GitHub API: stars, forks, description, primary language.  
- Detects tech stack (e.g., Python, Flask, JavaScript).  
- Computes **repository health score** based on code quality and file-level checks.  
- Provides **file-level insights** and suggestions.  

### Pull Request Analysis
- Input a PR URL to fetch all changed files.  
- Displays **additions, deletions, and total changes** per file.  
- JSON output rendered dynamically on the frontend.  
- Easily extendable to include file-level suggestions for PRs.  

---

## Demo
**Repository Analyzer**:  
- Input: `https://github.com/pallets/flask`  
- Outputs:  
  - Stars, forks, language  
  - Tech stack  
  - Health score  
  - File-level explanations and suggestions  

**Pull Request Analyzer**:  
- Input: `https://github.com/pallets/flask/pull/5200`  
- Outputs JSON summary of files changed, additions, deletions, and total changes.

> **Tip:** Add a `GITHUB_TOKEN` in `.env` to increase API rate limits.

---

## Installation
1. Clone the repository:  
```bash
git clone https://github.com/<your-username>/AI_githubRepo_analyzer.git
cd AI_githubRepo_analyzer

2. Create a virtual environment and activate it:

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate

3. Install dependencies:

pip install -r requirements.txt

(Optional) Add a .env file with your GitHub token to increase API rate limits:

4. GITHUB_TOKEN=your_personal_access_token

Run the Flask app:

5. python src/flask/app.py

Open your browser at http://127.0.0.1:5000

Usage

1. Repository Analysis

Enter a GitHub repository URL.

View tech stack, health score, and file-level suggestions.

2. Pull Request Analysis

Enter a GitHub Pull Request URL.

View changed files along with additions, deletions, and total changes.

Project Structure
AI_githubRepo_analyzer/
│
├── src/
│   └── flask/
│       ├── views.py           # Flask endpoints for repo & PR analysis
│       ├── repo_analyzer.py   # Repository analysis logic
│       └── templates/         # HTML templates
│
├── static/
│   └── js/
│       └── pr_analyzer.js     # Handles PR form submission & frontend rendering
│
├── .env                       # Optional: GitHub token
├── requirements.txt
└── README.md
Future Improvements

-Extend PR analysis to include file-level insights similar to repository analysis.

-Color-coded tables and visualizations for additions/deletions in PRs.

-Support multi-language repositories for tech stack detection.

-Integration with CI/CD pipelines for automated repo health checks.

Contributing

Contributions are welcome!

Fork the repository

Create a new branch for your feature or bugfix

Submit a pull request describing your changes