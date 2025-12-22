#!/usr/bin/env python3
"""
Generate a markdown summary of gene panel changes between two git refs.

This script compares panel files (`panels/*.txt`) across two commits and
reports added and removed genes for each changed panel.  The output is
intended to be used in continuous integration to comment on pull requests.

Usage:
    python scripts/panel_diff.py <base_ref> <head_ref>

If either argument is omitted the script exits with an error.  The working
directory must be a git repository with the panels present.  The script has
no external dependencies beyond the Python standard library and git being
installed.

Example output:

    ## panels/cardiomyopathy.txt
    Added: GENE1, GENE2
    Removed: GENE3

New files list all genes under "Added"; deleted files list all genes under
"Removed".  If a panel changes only comments or whitespace then no output
will be generated for that file.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Set, Tuple


def read_genes_from_blob(ref: str, path: str) -> Set[str]:
    """Return a set of gene symbols from a file at the given ref.

    Comment lines (starting with '#') and empty lines are ignored.  Whitespace
    is stripped.  If the file does not exist at the given ref, an empty set
    is returned.
    """
    try:
        # Use git show to get file content at given ref
        output = subprocess.check_output(["git", "show", f"{ref}:{path}"], stderr=subprocess.STDOUT)
        text = output.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError:
        return set()
    genes: Set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        genes.add(line)
    return genes


def list_changed_panel_files(base: str, head: str) -> List[str]:
    """List panel files (.txt) that changed between two refs."""
    try:
        output = subprocess.check_output([
            "git", "diff", "--name-only", base, head, "--", "panels"
        ])
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e.output}", file=sys.stderr)
        sys.exit(1)
    files = [f for f in output.decode().splitlines() if f.endswith(".txt")]
    return files


def generate_diff(base: str, head: str) -> str:
    """Generate a markdown summary of gene additions/removals between refs."""
    lines: List[str] = []
    changed_files = list_changed_panel_files(base, head)
    for file in sorted(changed_files):
        base_genes = read_genes_from_blob(base, file)
        head_genes = read_genes_from_blob(head, file)
        added = sorted(head_genes - base_genes)
        removed = sorted(base_genes - head_genes)
        # Skip if no content changes (e.g. only comments or whitespace)
        if not added and not removed:
            continue
        lines.append(f"## {file}")
        if added:
            lines.append("Added: " + ", ".join(added))
        if removed:
            lines.append("Removed: " + ", ".join(removed))
        lines.append("")  # blank line between files
    return "\n".join(lines).strip() + "\n" if lines else ""


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python scripts/panel_diff.py <base_ref> <head_ref>", file=sys.stderr)
        sys.exit(1)
    base, head = sys.argv[1:3]
    summary = generate_diff(base, head)
    if summary:
        print(summary)
    else:
        print("No gene changes detected.")


if __name__ == "__main__":
    main()