---
name: repo-layout
description: "Monorepo or multi-repo layout: changed-only builds, shared libraries, versioning. Use when setting up repo structure, splitting or merging repos, or deciding how shared code is built and released."
verified: 2026-11-07
---

# Repo layout: monorepo or polyrepo

Tool versions checked 2026-11-07 (npm registry): Nx and Turborepo are the
JavaScript and TypeScript options; Bazel targets large, multi-language repos.
Check each tool's docs for its current version before adopting it.

## Decide

- **Monorepo** when teams change shared code together, several apps share
  libraries, or you want one CI and one place for standards. Costs: build tooling
  and discipline to keep the graph clean.
- **Polyrepo** when teams and release cycles are independent, access must be
  separated (for example, regulated data), or the tooling budget is small.
  Costs: shared libraries need explicit versioning and compatibility testing.
- Small team and one product: start with a monorepo. It is easier to split later
  than to merge.

## Monorepo rules

- Build and test only what changed plus its dependents (affected-only CI). Use
  the tool's graph (Nx, Turborepo or Bazel) rather than hand-written path filters.
- One lock file per package manager at the root. Keep dependency versions aligned
  through a workspace feature, not copies.
- `CODEOWNERS` for each directory, so shared code has named reviewers.
- Keep package boundaries explicit: a package imports another only through its
  public entry point.

## Polyrepo rules

- Publish shared libraries with semantic versions. Consumers upgrade on purpose.
- Test compatibility before release: consumer tests in the consuming repo, or
  contract tests (see `architecture-monolith-vs-services` and `repo-api-and-ui`).
- Keep a short list of shared standards (lint, CI template, security policy) that
  every repo copies from one template repo.

## Either way

- One README per repo or package with what it is, how to build, how to test.
- Renovate or Dependabot for dependency updates, grouped so PRs stay reviewable.

## Setting one up

`project-structure` creates and checks the layout: a Python workspace, a TypeScript
workspace or a Rust workspace with apps, packages and written dependency rules. Use it
after you decide on a monorepo.
