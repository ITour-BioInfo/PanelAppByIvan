# Gene Panels Directory

This directory contains gene panels for the **PanelAppByIvan** project.  Each panel is stored as a plain text file (`.txt`) containing one gene symbol per line.  The goal is to keep the format extremely simple so that it can be edited by anyone using a basic text editor, spreadsheet software or through the optional panel editor web application.

## Panel file format

* Each non‑empty, non‑comment line **must** contain exactly one gene symbol with no spaces or tabs.  Gene symbols are case sensitive and should follow HGNC conventions.
* Lines starting with `#` are treated as comments and are ignored by tooling.  Comment lines may be used for notes or section headers within a panel.
* Blank lines are ignored and may be used to group genes visually.  However, try to avoid excessive spacing as this can introduce confusion.
* Files **must** end with a single newline character.  Many text editors add this automatically, but please double‑check to avoid validation failures.
* Genes should be listed in alphabetical order (case‑insensitive) to make diffs easy to read.  The validation script will flag any out‑of‑order entries.
* Duplicate gene symbols are not allowed.  The validator will fail on exact duplicates and warn about case‑insensitive duplicates (e.g. `abc` vs `ABC`).

### Editing in Excel or other spreadsheet software

To edit a panel using a spreadsheet application such as Excel or LibreOffice:

1. Open the `.txt` file as a single‑column spreadsheet.  Most editors will detect that it is a plain text file and offer to split by lines.
2. Edit the gene list in the single column.  Avoid adding extra whitespace or multiple words per cell.
3. When saving, choose **Text (Tab delimited)** or **CSV** and ensure that there is exactly one gene symbol per line.  Do not include a header row.
4. Re‑open the saved file in a text editor to confirm that the format matches the rules above (no extra commas or quotes).

## Index and metadata

A simple catalog of available panels is kept in `index.yml`.  Each entry includes an identifier, a human readable title, the filename of the panel, and an optional list of owners (GitHub usernames or teams) responsible for reviewing changes.  Feel free to add additional metadata fields if they become useful in the future.

## Validation

A Python script (`scripts/validate_panels.py`) is provided to check that all panels conform to the rules above.  It runs automatically in continuous integration (CI) and will fail the build if issues are detected.  You can also run it locally before committing changes:

```bash
python scripts/validate_panels.py
```

## Submitting changes

Changes to panels should be made on a feature branch and opened as a pull request.  The PR template in this repository asks for basic information about which panels were modified and why.  Continuous integration will validate the panels and provide a summary of added/removed genes.  Once approved by a code owner, the PR can be merged.
