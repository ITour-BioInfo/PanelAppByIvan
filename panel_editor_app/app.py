"""
Simple web application for editing gene panels without a GitHub account.

This FastAPI app provides a minimal interface to list panels stored in the
repository, edit them via a textarea, preview changes versus the current
main branch and submit a change by creating a branch and pull request
through the GitHub API.  A shared password (provided via the APP_PASSWORD
environment variable) protects the interface from unauthorised use.
"""

from __future__ import annotations

import base64
import datetime as dt
import os
import pathlib
from typing import Dict, List, Optional, Tuple

import requests
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates


# Configure directories
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
PANELS_DIR = ROOT_DIR / "panels"

# Authentication
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify that provided basic auth password matches APP_PASSWORD."""
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        raise HTTPException(status_code=500, detail="APP_PASSWORD not configured")
    correct = credentials.password == app_password
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class GitHubClient:
    """Minimal wrapper around GitHub REST API for creating branches and PRs."""
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "panel-editor-app",
        }

    def _request(self, method: str, url: str, **kwargs):
        resp = requests.request(method, url, headers=self.headers, **kwargs)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.json().get('message', resp.text))
        return resp.json()

    def get_branch_sha(self, branch: str) -> str:
        url = f"{self.base_url}/git/ref/heads/{branch}"
        data = self._request("GET", url)
        return data["object"]["sha"]

    def create_branch(self, new_branch: str, base_sha: str) -> None:
        url = f"{self.base_url}/git/refs"
        payload = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
        self._request("POST", url, json=payload)

    def create_or_update_file(self, path: str, content: str, message: str, branch: str) -> None:
        url = f"{self.base_url}/contents/{path}"
        b64_content = base64.b64encode(content.encode("utf-8")).decode()
        payload = {
            "message": message,
            "content": b64_content,
            "branch": branch,
        }
        self._request("PUT", url, json=payload)

    def create_pull_request(self, title: str, body: str, head: str, base: str) -> str:
        url = f"{self.base_url}/pulls"
        payload = {"title": title, "body": body, "head": head, "base": base}
        data = self._request("POST", url, json=payload)
        return data.get("html_url")


def list_panels() -> List[pathlib.Path]:
    return sorted([p for p in PANELS_DIR.iterdir() if p.suffix == ".txt"])


def read_panel_file(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_genes(content: str) -> List[str]:
    genes: List[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        genes.append(line)
    return genes


def diff_genes(original: str, updated: str) -> Tuple[List[str], List[str]]:
    """Return (added, removed) lists of genes between two contents."""
    orig_set = set(parse_genes(original))
    new_set = set(parse_genes(updated))
    added = sorted(list(new_set - orig_set))
    removed = sorted(list(orig_set - new_set))
    return added, removed


def validate_content(content: str) -> Optional[str]:
    """Validate panel content.  Return error message if invalid, else None."""
    lines = content.splitlines()
    # Must end with newline
    if content and not content.endswith("\n"):
        return "File must end with a newline"
    seen: List[str] = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if any(ch.isspace() for ch in stripped):
            return f"Line {i}: '{stripped}' contains whitespace"
        # duplicate check
        if stripped in seen:
            return f"Duplicate gene '{stripped}' on line {i}"
        # case-insensitive duplicate
        lower = stripped.lower()
        for s in seen:
            if s.lower() == lower:
                # not fatal but return warning message in error string
                return f"Gene '{stripped}' duplicates '{s}' ignoring case at line {i}"
        seen.append(stripped)
    # check sorted
    keys = [g.lower() for g in seen]
    if keys != sorted(keys):
        return "Genes must be sorted alphabetically (case-insensitive)"
    return None


templates = Jinja2Templates(directory=str(pathlib.Path(__file__).resolve().parent / "templates"))
app = FastAPI()


@app.get("/")
def index(request: Request, username: str = Depends(verify_credentials)):
    panels = list_panels()
    return templates.TemplateResponse("list.html", {"request": request, "panels": panels, "username": username})


@app.get("/edit/{panel_name}")
def edit_panel(panel_name: str, request: Request, username: str = Depends(verify_credentials)):
    panel_path = PANELS_DIR / panel_name
    if not panel_path.exists() or panel_path.suffix != ".txt":
        raise HTTPException(status_code=404, detail="Panel not found")
    content = read_panel_file(panel_path)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "panel_name": panel_name,
        "content": content,
        "error": None,
        "added": [],
        "removed": [],
    })


@app.post("/edit/{panel_name}")
def save_panel(panel_name: str, request: Request, content: str = Form(...), username: str = Depends(verify_credentials)):
    panel_path = PANELS_DIR / panel_name
    if not panel_path.exists() or panel_path.suffix != ".txt":
        raise HTTPException(status_code=404, detail="Panel not found")
    # Ensure newline at EOF for diff and validation
    if not content.endswith("\n"):
        content += "\n"
    # Validate
    error_msg = validate_content(content)
    original = read_panel_file(panel_path)
    added, removed = diff_genes(original, content)
    if error_msg:
        # Show the form again with error and diff preview
        return templates.TemplateResponse("edit.html", {
            "request": request,
            "panel_name": panel_name,
            "content": content,
            "error": error_msg,
            "added": added,
            "removed": removed,
        })
    # Submit change via GitHub
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    token = os.getenv("GITHUB_TOKEN")
    base_branch = os.getenv("BASE_BRANCH", "main")
    if not (owner and repo and token):
        raise HTTPException(status_code=500, detail="GitHub client configuration missing")
    gh = GitHubClient(owner, repo, token)
    try:
        base_sha = gh.get_branch_sha(base_branch)
        timestamp = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        branch_name = f"panel-edit-{panel_name.replace('.txt','')}-{timestamp}"
        gh.create_branch(branch_name, base_sha)
        commit_message = f"Update panel {panel_name} via web editor"
        file_path = f"panels/{panel_name}"
        gh.create_or_update_file(file_path, content, commit_message, branch_name)
        pr_title = f"Edit panel {panel_name}"
        pr_body = f"Automated update of panel `{panel_name}` via web editor.\n\nAdded genes: {', '.join(added) or 'none'}\nRemoved genes: {', '.join(removed) or 'none'}"
        pr_url = gh.create_pull_request(pr_title, pr_body, branch_name, base_branch)
    except HTTPException as exc:
        # propagate HTTP errors as warnings to the user
        return templates.TemplateResponse("edit.html", {
            "request": request,
            "panel_name": panel_name,
            "content": content,
            "error": f"Submission failed: {exc.detail}",
            "added": added,
            "removed": removed,
        })
    # Redirect to PR URL
    return RedirectResponse(url=pr_url, status_code=303)