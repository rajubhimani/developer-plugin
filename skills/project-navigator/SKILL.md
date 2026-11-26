---
name: project-navigator
description: Find projects in a projects folder through small docs under docs/ instead of rescanning. Use when asked about several projects, where something lives, how projects connect, or what command runs a project.
verified: 2026-11-07
---

# Project navigator

The projects folder has a `docs/` folder with small files. Use the smallest
file that answers the question. Never read all of them.

| Question | Read |
|---|---|
| Which projects exist, where are they? | `docs/INDEX.md` (short) |
| What is this project, its path, stack, what else is in its folder? | `docs/projects/<name>/INDEX.md` |
| How do I build, test or run it? | `docs/projects/<name>/commands.md` |
| Facts you kept about it | `docs/projects/<name>/notes.md` |
| Does project A depend on project B? | `docs/links.md` |
| Shared conventions, things to remember | `docs/notes.md` |

Each project folder can hold more topic files. Its `INDEX.md` lists them, so
open the one that matches the question.

The umbrella folder also has an `AGENTS.md` (and a `CLAUDE.md` that imports
it). They point here, so you rarely need to find this skill first.

## Steps

1. Start with `docs/INDEX.md`, then the project's `INDEX.md`.
2. Open only the project file you need. Open the repo's own `CLAUDE.md`,
   `AGENTS.md` or `README.md` only if the project file does not
   answer the question.
3. If `docs/` is missing, or a project is not listed, run
   `make workspace WS_ROOT=<folder>`. Do not scan the folder by hand.
4. Refresh the generated files with `make navigator` when the folder changes.
   This never touches the notes sections.
5. Write a fact that spans projects into `docs/notes.md`. Write a fact about one
   project into `docs/projects/<name>/notes.md`. Keep each note to one line.
   For a long topic, add its own file in that project folder and link it from
   the project's `INDEX.md`.

## Rules

- Prefer these small files over searching the repos. A search costs more tool
  calls and tokens.
- Treat the docs as a snapshot. Check a project's files before relying on a
  detail that could have changed, such as a version or a path.
