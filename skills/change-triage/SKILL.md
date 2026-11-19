---
name: change-triage
description: Pick the lightest safe path for a change (hotfix, docs/config edit, small change, or feature) with two questions, and confirm it with the user in one reply. Use when starting any change, before writing a task or code.
verified: 2026-11-17
---

# Change triage

Heavy process on a one-line fix wastes time; light process on a risky change
causes incidents. Choose the path before you start.

## Routes

| Route | Take it when | What it needs |
|---|---|---|
| Hotfix | Users are hurt by a defect now | `debug-failure`, a failing test, review |
| Docs, config or copy | Only documentation, configuration or user-facing wording changes, with no logic | The edit and a review of the diff |
| Research | Whether to build it is still open | A short note and a decision |
| Small change | No trigger below, and one behaviour at one public boundary | One requirement line, a failing test first, then the build |
| Feature | A trigger below, or more than one task | Requirements, a short design, tasks (see `feature-workflow`) |

Text a program reads (a JSON key, an error code, parsed output) is a contract,
not copy. It takes the small-change route with a test.

## The two questions

1. Does it trip a design trigger? New component or service, a swappable
   boundary, branching that will keep growing, a data migration, a new
   environment variable or deploy artifact, or anything touching authentication,
   personal data, secrets, crypto or a control other code relies on.
2. Is it one task delivering one behaviour at one public boundary (one command,
   endpoint or screen)? Size is not the test: a one-line change can open a new
   seam.

No trigger and one task: small change. Otherwise: feature.

## Confirm in one reply

State: the route and the trigger that set it (or "no trigger"), the requirement
line with its examples, the risk (low, medium, high) and how to roll it back
(revert, switch off, or fix forward, and why that is safe). Wait for the
user's confirmation or correction before creating tasks or code.

## Waivers

The user may waive a trigger. Proceed on the lighter route and record their
reason in the task. Never waive one on your own judgment.
