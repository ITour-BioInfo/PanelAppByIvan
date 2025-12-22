#!/usr/bin/env python3
"""
Validation script for gene panel files.

This script scans all `.txt` files in the `panels/` directory, enforcing
formatting rules to keep diffs deterministic and panels consistent:

* Lines beginning with `#` are ignored as comments.
* Empty lines are ignored.
* Each non‑comment line must contain exactly one token (no spaces or tabs).
* Files must end with a newline character.
* Genes must be sorted alphabetically (case‑insensitive) to make diffs simple.
* Duplicate gene entries are not allowed (case‑sensitive) and case‑insensitive
  duplicates generate warnings.

If any errors are detected the script exits with a non‑zero status and
prints clear error messages including the filename and line number.

Usage:
    python scripts/validate_panels.py

This script is intentionally simple and has no external dependencies beyond
the Python standard library.
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple


PANELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "panels")


class ValidationError(Exception):
    """Raised when a validation error occurs."""
    pass


def read_panel(filepath: str) -> Tuple[List[str], List[str]]:
    """Read a panel file and return a tuple of (gene_lines, warnings).

    Comment lines and empty lines are skipped.  The returned list contains
    only gene symbols as they appear in the file (with surrounding whitespace
    stripped).  A list of warning messages is returned separately.
    """
    warnings: List[str] = []
    genes: List[str] = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw_content = f.read()
        # Check newline at end of file
        if raw_content and not raw_content.endswith("\n"):
            raise ValidationError(f"{filepath}: file must end with a newline\n")
        # Reset pointer and iterate lines
        f.seek(0)
        for line_num, line in enumerate(f, start=1):
            line = line.rstrip("\n").strip()
            if not line or line.startswith("#"):
                continue
            # Disallow any whitespace inside the gene symbol
            if any(ch.isspace() for ch in line):
                raise ValidationError(
                    f"{filepath}:{line_num}: invalid entry '{line}' (contains whitespace)."
                )
            # Check for duplicate ignoring case
            lower = line.lower()
            for existing in genes:
                if existing == line:
                    raise ValidationError(
                        f"{filepath}:{line_num}: duplicate gene '{line}' detected."
                    )
                if existing.lower() == lower:
                    warnings.append(
                        f"{filepath}:{line_num}: warning – gene '{line}' differs only in case from '{existing}'."
                    )
            genes.append(line)
    return genes, warnings


def validate_sorted(genes: List[str], filepath: str) -> None:
    """Ensure genes are sorted case‑insensitively.  Raise ValidationError if not."""
    prev: str | None = None
    for idx, gene in enumerate(genes):
        key = gene.lower()
        if prev is not None and key < prev:
            raise ValidationError(
                f"{filepath}: genes must be sorted alphabetically (case‑insensitive)."
                f" Found out‑of‑order entry '{gene}' at position {idx + 1}."
            )
        prev = key


def main() -> None:
    errors: List[str] = []
    all_warnings: List[str] = []

    if not os.path.isdir(PANELS_DIR):
        print(f"Panels directory not found at {PANELS_DIR}", file=sys.stderr)
        sys.exit(1)

    for filename in os.listdir(PANELS_DIR):
        # Only validate plain text panel files
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(PANELS_DIR, filename)
        try:
            genes, warnings = read_panel(path)
            all_warnings.extend(warnings)
            validate_sorted(genes, path)
        except ValidationError as e:
            errors.append(str(e))

    for w in all_warnings:
        print(w, file=sys.stderr)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    print("All panels validated successfully.")


if __name__ == "__main__":
    main()