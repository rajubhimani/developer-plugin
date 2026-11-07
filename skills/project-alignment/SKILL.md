---
name: project-alignment
description: Keep a project's requirements, tests, docs and hygiene aligned, using the align check and the requirement ID rules. Use when adding or changing requirements or tests, when make align or make check fails, or when asked whether the project meets its requirements.
verified: 2026-11-07
---

# Project alignment

`make align` runs `tests/alignment/`. It checks that the project still matches
its requirements, its docs and the plugin's guidelines. `make check` runs it too.

## What it checks

- Every requirement in `docs/requirements.md` has at least one test naming its ID.
- Every requirement ID named in a test exists. Requirement IDs are unique.
- Relative links in `docs/` point at files that exist.
- The project is a git repository, has a README title, the standard make targets,
  a `.gitignore` that ignores `.env`, and a lock file for its language.
- Container and CI files follow the docker, compose and ci-cd skills.

## Working with it

1. Add a requirement as one line, `- REQ-NNN: statement`, with the next free ID.
2. Write the test first, with a comment naming the ID, for example `# REQ-NNN`.
3. Run `make align`. Fix the failing check, not the check itself.
4. Only skip a check when the file it needs does not exist in this project.

## Rules

- Never delete a requirement ID that tests still name. Mark it removed with a
  reason and remove the tests with it, in the same change.
- Do not add a test that names a requirement only to pass the check. The test must
  check the requirement.
- Report which checks ran and which were skipped.
