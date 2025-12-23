# GitHub setup checklist

After this reset merges, configure repository governance:

1. **Protect the default branch.** Enable branch protection and block force pushes. See GitHub docs on [about protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) and [managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).
2. **Require pull request reviews.** Set minimum approvals to at least one. Reference [about protected branches](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
3. **Require status checks to pass.** Add the `Validate panels` workflow job as a required status check. Learn more in [about status checks](https://docs.github.com/articles/about-status-checks).
4. **Optional: require code owner reviews.** Once CODEOWNERS is populated, enforce reviews from owners. See [about code owners](https://docs.github.com/articles/about-code-owners).
5. **Automatic token usage.** For Actions, rely on GitHub’s built-in tokens as described in [automatic token authentication](https://docs.github.com/actions/security-guides/automatic-token-authentication).

These settings help ensure panel updates remain reviewed and validated before merging.
