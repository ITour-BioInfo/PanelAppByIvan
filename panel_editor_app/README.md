# Panel Editor Web Application (Optional)

This directory contains an optional, lightweight web application that lets users
edit gene panels without needing a GitHub account.  It is designed to be
self‑hosted behind a simple password and works by creating a new branch and
pull request on GitHub using a personal access token.

## Features

* List available panels defined in `panels/`.
* View and edit a panel’s gene list in a web browser.
* Preview which genes have been added or removed compared to the current main branch.
* Submit changes: creates a new branch, commits the updated panel file, and
  opens a pull request against the base branch.

## Running locally

The app is built with FastAPI and Jinja2 templates.  You can run it directly
with Uvicorn or via Docker.  A minimal set of dependencies is listed in
`requirements.txt`.

### Environment variables

| Variable | Description |
|---------|-------------|
| `GITHUB_OWNER` | GitHub username or organisation that owns the repository. |
| `GITHUB_REPO` | Name of the repository (e.g. `PanelAppByIvan`). |
| `GITHUB_TOKEN` | Personal access token with repo permissions. |
| `BASE_BRANCH` | Target branch for pull requests (default: `main`). |
| `APP_PASSWORD` | Password required to access the web UI. |
| `APP_PORT` | Port on which the server should listen (default: `8000`). |

### Running with Docker

To build and run the app using Docker:

```bash
docker build -t panel-editor ./panel_editor_app
docker run -e GITHUB_OWNER=... -e GITHUB_REPO=... -e GITHUB_TOKEN=... -e APP_PASSWORD=changeme -p 8000:8000 panel-editor
```

Alternatively, `docker-compose.yml` is provided for convenience:

```bash
APP_PASSWORD=changeme GITHUB_OWNER=... GITHUB_REPO=... GITHUB_TOKEN=... docker-compose up
```

### Development

Run the app directly with Python:

```bash
export APP_PASSWORD=changeme
uvicorn panel_editor_app.app:app --reload
```

At this stage the editor relies on a valid GitHub token to create branches
and pull requests.  The network calls are wrapped in a simple `GitHubClient`
class in `app.py`.  If network connectivity is unavailable the submission
feature will raise an exception.  Validation is performed using the same
logic as `scripts/validate_panels.py`.