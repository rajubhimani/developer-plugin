---
name: code-review-checklist
description: Review a code change for correctness, tests, security and clarity using a fixed checklist. Use when asked to review a diff, branch or pull request.
verified: 2026-11-07
---

# Code review checklist

1. Read the full diff before commenting. Note what the change is meant to do.
2. Correctness: check edge cases, error handling and off-by-one errors.
3. Tests: confirm changed behaviour has a test, and that the tests can fail.
4. Security: look for unvalidated input, secrets in code, and unsafe shell or SQL.
5. Clarity: flag names, dead code and comments that explain what instead of why.
6. Report findings ordered by severity, each with a file and line reference.
   Say plainly when nothing was found and what was not checked.
