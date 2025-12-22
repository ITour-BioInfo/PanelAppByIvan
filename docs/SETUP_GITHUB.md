# Recommended GitHub settings

To ensure panel changes are reviewed and recorded properly, we recommend enabling the following settings on the repository's default branch (typically **main**).  These settings can be configured under *Settings → Branches* in the GitHub UI.

1. **Require a pull request before merging**
   * Enable *Require pull request reviews before merging*.
   * Optionally require the branch to be up to date before merging to ensure that CI has run on the latest code.
2. **Require approvals**
   * Set *Required approvals* to at least **1**.  This ensures that another curator reviews the panel changes.
   * Enable *Dismiss stale pull request approvals when new commits are pushed* to force re‑review after updates.
3. **Require review from Code Owners**
   * Enable *Require review from Code Owners*.  This will automatically request reviews from the owners specified in `.github/CODEOWNERS` for any files they cover (including `panels/*`).
4. **Status checks**
   * Ensure that the `Validate gene panels` workflow passes before allowing merges.  You can do this by selecting it under *Status checks that must pass before merging*.

These settings help maintain a clear audit trail of who changed which genes and why.  They also prevent accidental direct pushes to the main branch without review.