#!/usr/bin/env python3
"""Validate panel text files.

Rules:
- Ignore blank lines and comment lines starting with '#'.
- Each gene line must be a single token without spaces or tabs.
- No duplicate genes (case-sensitive). Case-insensitive duplicates are warned.
- Files must end with a newline.
- Gene lists must be sorted case-insensitively for clean diffs.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

PANELS_DIR = Path(__file__).resolve().parent.parent / "panels"


def load_panel(path: Path) -> Tuple[List[str], List[Tuple[int, str]], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    genes: List[str] = []

    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        errors.append(f"{path}: file must end with a newline")

    seen: Dict[str, int] = {}
    seen_lower: Dict[str, int] = {}

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lstrip("\ufeff")  # handle optional BOM on the first line
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if " " in line or "\t" in line:
            errors.append(f"{path}:{lineno}: gene entries must not contain spaces or tabs")
            continue

        gene = stripped

        if gene in seen:
            errors.append(
                f"{path}:{lineno}: duplicate gene '{gene}' (previous at line {seen[gene]})"
            )
        else:
            seen[gene] = lineno

        lower = gene.lower()
        if lower in seen_lower and seen_lower[lower] != lineno and gene not in seen:
            warnings.append(
                f"{path}:{lineno}: possible case-insensitive duplicate of line {seen_lower[lower]}: '{gene}'"
            )
        else:
            seen_lower[lower] = lineno

        genes.append(gene)

    sorted_genes = sorted(genes, key=str.lower)
    if genes != sorted_genes:
        errors.append(f"{path}: genes must be sorted case-insensitively")

    return genes, errors, warnings


def validate_panels() -> int:
    if not PANELS_DIR.exists():
        print(f"Panels directory not found: {PANELS_DIR}")
        return 1

    panel_files = sorted(PANELS_DIR.glob("*.txt"))
    if not panel_files:
        print("No panel files found in panels/*.txt")
        return 1

    all_errors: List[str] = []
    all_warnings: List[str] = []

    for path in panel_files:
        _, errors, warnings = load_panel(path)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for msg in all_errors:
        print(f"ERROR: {msg}")

    for msg in all_warnings:
        print(f"WARNING: {msg}")

    if all_errors:
        print(f"Validation failed: {len(all_errors)} error(s), {len(all_warnings)} warning(s)")
        return 1

    print(f"Validation passed for {len(panel_files)} file(s).")
    if all_warnings:
        print(f"Completed with {len(all_warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(validate_panels())
