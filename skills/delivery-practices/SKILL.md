---
name: delivery-practices
description: Ship in small, safe steps: short-lived branches, flags, progressive rollout, fast rollback, the four delivery measures. Use when planning a release, sizing a pull request, or reviewing delivery health.
verified: 2026-11-19
---

# Delivery practices

Research on delivery teams links small batches, short-lived branches and fast
feedback to both speed and stability. The evidence is from surveys, so it shows
correlation, not proof; use it to choose habits, then measure your own results.

## Rules

1. **Small changes.** One purpose per change, reviewable in minutes (see
   `git-workflow`). Large work is cut into slices that each leave the product
   working.
2. **Short-lived branches.** Merge to the main line at least daily where you can;
   a branch alive for days is a merge risk. Keep main always releasable.
3. **Separate deploy from release.** Ship unfinished work dark behind a feature
   flag, then turn it on gradually. A flag has an owner and a removal date; remove
   it after rollout, or flags become debt.
4. **Roll out in steps:** a small share of traffic or a pilot group, watch the
   health signals (see `observability`), then widen. Define in advance what makes
   you stop.
5. **Every release is reversible.** Know the rollback (code, flag or schema step)
   before you ship, and practise it. Prefer roll forward by switching a flag off.
6. **Automate the path** from commit to production: build once, test, scan, deploy,
   verify (see `ci-cd`). A step done by hand will be skipped under pressure.
7. **Keep the pipeline fast and trusted.** Fix or delete flaky tests the day they
   appear; a slow or flaky pipeline makes people batch changes.
8. **Blameless reviews.** After an incident, write what happened, why the system
   let it, and what changes; fix the system, not a person.

## Measure, carefully

| Measure | Question |
|---|---|
| Lead time for changes | How long from commit to running in production? |
| Deploy frequency | How often do we ship? |
| Change failure rate | What share of changes need a fix, rollback or hotfix? |
| Time to restore | How fast do we recover from a failed change? |

- Track the trend per team, not a league table; never use them to rank people.
- Pair speed with stability. Faster with a rising failure rate is not better.
- Using AI help raises output; its benefit depends on keeping changes small and
  reviewed (see `ai-assisted-development`).

## Release readiness

Before a change goes out, the description answers: what changes for users, how
we know it works, how we undo it, and who is watching. The deploy reviewer checks
it (see `agent-handoff`).

## Related

`git-workflow`, `ci-cd`, `versioning-release`, `change-triage`, `debug-failure`.
