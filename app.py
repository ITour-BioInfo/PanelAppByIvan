from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from flask import Flask, abort, request, send_from_directory

app = Flask(__name__)

PANELS_DIR = Path(__file__).resolve().parent / "panels"
SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")


def render_page(title: str, body: str) -> str:
    style = """
    <style>
      body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 1.5rem; }
      h1, h2, h3 { margin-bottom: 0.4rem; }
      ul { padding-left: 1.2rem; }
      .panel-card { border: 1px solid #ddd; padding: 0.75rem; margin-bottom: 0.75rem; border-radius: 4px; }
      .meta { color: #444; font-size: 0.95rem; }
      pre { background: #f7f7f7; padding: 0.75rem; border-radius: 4px; overflow: auto; }
      form { margin-bottom: 1rem; }
      input[type=text] { padding: 0.4rem; width: 250px; }
      button { padding: 0.4rem 0.7rem; }
      .links a { margin-right: 0.8rem; }
    </style>
    """
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>{style}</head><body><h1>{html.escape(title)}</h1>{body}</body></html>"


def safe_panel_path(slug: str) -> Path:
    if not SLUG_PATTERN.match(slug):
        abort(404)
    panel_path = (PANELS_DIR / f"{slug}.txt").resolve()
    if not str(panel_path).startswith(str(PANELS_DIR.resolve())):
        abort(400)
    if not panel_path.exists():
        abort(404)
    return panel_path


def parse_panel(path: Path) -> Tuple[Dict[str, str], List[str]]:
    metadata: Dict[str, str] = {}
    genes: List[str] = []
    metadata_section = True

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.lstrip("\ufeff")
        stripped = line.strip()

        if not stripped:
            continue

        if metadata_section and stripped.startswith("#"):
            content = stripped.lstrip("#").strip()
            if ":" in content:
                key, value = content.split(":", 1)
                metadata[key.strip()] = value.strip()
                continue
            metadata_section = False
            # fall through to comment handling

        if stripped.startswith("#"):
            continue

        metadata_section = False
        genes.append(stripped)

    return metadata, genes


def collect_panels() -> List[Dict[str, object]]:
    panels: List[Dict[str, object]] = []
    for path in sorted(PANELS_DIR.glob("*.txt")):
        metadata, genes = parse_panel(path)
        slug = path.stem
        panels.append(
            {
                "slug": slug,
                "title": metadata.get("title", slug.replace("_", " ").title()),
                "metadata": metadata,
                "genes": genes,
            }
        )
    return panels


@app.route("/")
def index() -> str:
    query = request.args.get("q", "").strip()
    panels = collect_panels()

    q_lower = query.lower()
    gene_matches = []
    name_matches = []

    if query:
        for panel in panels:
            if q_lower in panel["slug"].lower() or q_lower in str(panel["title"]).lower():
                name_matches.append(panel)
            if any(gene.lower() == q_lower for gene in panel["genes"]):
                gene_matches.append(panel)

    body_parts = [
        "<form method='get'>",
        "<input type='text' name='q' placeholder='Search by panel or gene' value='" + html.escape(query) + "'>",
        "<button type='submit'>Search</button>",
        "</form>",
    ]

    if query:
        body_parts.append(f"<h2>Search results for '{html.escape(query)}'</h2>")
        if gene_matches:
            body_parts.append("<h3>Panels containing the gene</h3><ul>")
            for panel in gene_matches:
                body_parts.append(
                    f"<li><a href='/panels/{html.escape(panel['slug'])}'>"
                    f"{html.escape(panel['title'])}</a> (slug: {html.escape(panel['slug'])})" + "</li>"
                )
            body_parts.append("</ul>")
        else:
            body_parts.append("<p>No gene matches.</p>")

        if name_matches:
            body_parts.append("<h3>Panel name matches</h3><ul>")
            for panel in name_matches:
                body_parts.append(
                    f"<li><a href='/panels/{html.escape(panel['slug'])}'>"
                    f"{html.escape(panel['title'])}</a> (slug: {html.escape(panel['slug'])})" + "</li>"
                )
            body_parts.append("</ul>")
        else:
            body_parts.append("<p>No panel name matches.</p>")

    body_parts.append("<h2>All panels</h2>")
    for panel in panels:
        meta_title = html.escape(panel["title"])
        slug = html.escape(panel["slug"])
        body_parts.append(
            "<div class='panel-card'>"
            f"<h3><a href='/panels/{slug}'>{meta_title}</a></h3>"
            f"<div class='meta'>Slug: {slug}</div>"
            f"<div class='meta'>Genes: {len(panel['genes'])}</div>"
            "</div>"
        )

    return render_page("PanelApp-lite", "".join(body_parts))


@app.route("/panels/<slug>")
def panel_detail(slug: str) -> str:
    path = safe_panel_path(slug)
    metadata, genes = parse_panel(path)

    meta_list = "<ul>" + "".join(
        f"<li><strong>{html.escape(k)}:</strong> {html.escape(v)}</li>" for k, v in metadata.items()
    ) + "</ul>" if metadata else "<p>No metadata.</p>"

    gene_list_items = "".join(f"<li>{html.escape(g)}</li>" for g in genes)
    gene_section = "<ul>" + gene_list_items + "</ul>" if genes else "<p>No genes listed.</p>"

    links = (
        f"<div class='links'>"
        f"<a href='/panels/{html.escape(slug)}/raw'>Download raw</a>"
        f"<a href='/panels/{html.escape(slug)}/changelog'>Changelog</a>"
        "</div>"
    )

    body = (
        f"<div class='panel-card'><h2>{html.escape(metadata.get('title', slug.replace('_', ' ').title()))}</h2>"
        f"<div class='meta'>Slug: {html.escape(slug)}</div>"
        f"<h3>Metadata</h3>{meta_list}"
        f"<h3>Genes ({len(genes)})</h3>{gene_section}"
        f"{links}</div>"
    )

    return render_page(f"Panel: {slug}", body)


@app.route("/panels/<slug>/raw")
def panel_raw(slug: str):
    safe_panel_path(slug)  # validation
    return send_from_directory(PANELS_DIR, f"{slug}.txt", as_attachment=True)


@app.route("/panels/<slug>/changelog")
def panel_changelog(slug: str) -> str:
    path = safe_panel_path(slug)
    cmd = [
        "git",
        "log",
        "--follow",
        "--date=iso",
        "--pretty=%h %ad %an %s",
        "--",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        content = "<p>No git history found for this panel.</p>"
    else:
        lines = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split(" ", 1)
            commit = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            link = f"<a href='/panels/{html.escape(slug)}/diff/{html.escape(commit)}'>{html.escape(commit)}</a>"
            lines.append(f"{link} {html.escape(rest)}")
        content = "<pre>" + "\n".join(lines) + "</pre>"

    body = f"<div class='panel-card'><h2>Changelog for {html.escape(slug)}</h2>{content}</div>"
    return render_page(f"Changelog: {slug}", body)


@app.route("/panels/<slug>/diff/<commit>")
def panel_diff(slug: str, commit: str) -> str:
    path = safe_panel_path(slug)
    if not COMMIT_PATTERN.match(commit):
        abort(400, "Invalid commit format")

    cmd = ["git", "show", commit, "--", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        content = "<p>Unable to display diff for this commit/panel combination.</p>"
    else:
        content = "<pre>" + html.escape(result.stdout) + "</pre>"

    body = f"<div class='panel-card'><h2>Diff for {html.escape(slug)} @ {html.escape(commit)}</h2>{content}</div>"
    return render_page(f"Diff: {slug} @ {commit}", body)


if __name__ == "__main__":
    app.run(debug=True)
