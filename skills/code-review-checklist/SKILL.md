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
6. Refactors: search for every use of what was replaced (old names, string
   literals, constants), not only the lines in the diff. Check that a comment
   describing a removed item was moved or deleted, and that a type annotation is
   true for data loaded from files, not only for objects built in code.
7. Run the real entry points after a refactor and read their output. Passing
   tests can still hide a regression in logs, messages or printed values.
8. Run the formatter check after every edit, including edits made in an editor.
9. Reuse: flag a hand-written helper that a library the project already uses
   provides (mean, padding, counting), and any reduction over a possibly empty
   collection.
10. Report findings ordered by severity, each with a file and line reference.
   Say plainly when nothing was found and what was not checked.
