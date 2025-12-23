# PanelApp-lite

A minimal repository for hosting gene panels as plain text files with a tiny Flask UI and lightweight validation.

## Quickstart
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000/ in your browser.

## Panel format
- Panels live in `panels/*.txt`.
- Optional metadata lines at the top start with `# key: value`.
- One gene symbol per line after metadata.
- Blank lines and other comment lines starting with `#` are allowed.
- Keep genes sorted for clean diffs; files must end with a newline.

## Editing panels locally
1. Edit the relevant `panels/*.txt` file (metadata first, then genes).
2. Run the validator: `python scripts/validate_panels.py`.
3. Commit the change: `git commit -am "Update panels"`.

## How history powers the UI
The Flask UI reads panel files directly and uses Git history to populate the changelog and diff routes. After you commit changes to a panel, the `/panels/<slug>/changelog` and `/panels/<slug>/diff/<commit>` pages will reflect those commits.
