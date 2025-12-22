# Changelog

All notable changes to this repository are documented in this file.  The format loosely follows
the [Keep a Changelog](https://keepachangelog.com/) guidelines.  For a detailed view of gene
additions and removals, refer to the **Panel change summary** comment automatically posted on pull
requests by our CI.

## [Unreleased]

- Initial setup of panel repository:
  - Added `panels/` directory with sample panels for hereditary cancer, cardiomyopathy and epilepsy.
  - Added `panels/index.yml` catalog and `panels/README.md` with format guidelines.
  - Added validation script (`scripts/validate_panels.py`) and panel diff generator (`scripts/panel_diff.py`).
  - Added GitHub Actions workflows to validate panels and post change summaries.
  - Added governance scaffolding: PR template, code owners and setup instructions.
