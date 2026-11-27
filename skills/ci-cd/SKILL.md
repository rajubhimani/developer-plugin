---
name: ci-cd
description: "CI and CD practice: build once, gated pipelines, least-privilege tokens, pinned actions, OIDC, SBOM, promotion, rollback. Use when creating or changing pipelines, release automation or deployment configuration."
verified: 2026-11-07
---

# CI and CD

Sources checked 2026-11-07 are secondary (vendor and community guides on supply
chain security). Confirm action names, permissions and SLSA levels against
GitHub's Actions security documentation and the SLSA specification before use.
A starting template for GitHub Actions is in `references/github-actions.yml`.

## Pipeline shape

1. Lint, type-check and test on every pull request. Block merge on failure.
2. Build the artifact once, on the main branch or a release tag. Never rebuild
   for each environment.
3. Promote that same artifact through staging to production, with a
   manual approval for production if the team needs one.
4. Keep a rollback path: redeploy the previous artifact, or switch traffic back.

## Security

- Set the default token permission to read-only at the top of the workflow.
  Grant write permissions per job, only where needed.
- Pin third-party actions to a full commit SHA, with the version in a comment.
  Let Dependabot or Renovate propose the updates.
- Deploy with OIDC, not stored cloud keys: the job asks the cloud for a
  short-lived credential. Only the deploy job gets `id-token: write`.
- Do not run untrusted pull-request code with secrets. Avoid triggers that check
  out the pull request and then run it with elevated permissions.
- Never echo secrets. Pass untrusted input (issue titles, branch names) through
  environment variables, not directly into `run:` scripts.

## Supply chain

- Generate an SBOM for each release and attach it.
- Attach build provenance (SLSA). A practical baseline is SLSA Level 2 on a
  hosted CI platform; higher levels need stricter build isolation.
- Sign images or artifacts and verify the signature at deploy time, where the
  platform supports it.

## Speed

- Cache dependencies keyed on the lock file.
- Run jobs in parallel where they do not depend on each other.
- Use changed-only builds in monorepos (see `repo-layout`).

## Releases

- Trunk-based development: short-lived branches merged to main often.
- Semantic versioning for libraries and APIs. Generate release notes from
  commit or pull-request history.
- Protect the main branch: required reviews and passing checks.
