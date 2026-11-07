---
name: project-setup
description: Set up a new or existing project, or a folder of projects, with this plugin's standard files, git repository, make targets, docs and task tracking. Use when starting a project, adding the plugin's structure to a repo, or setting up docs for a folder that holds several repos.
verified: 2026-11-07
---

# Project setup

## One project

`make -C <plugin folder> init-project REPO=<project folder> LANG=<language>`

Languages: `python`, `go`, `rust`, `node`, `c`, `cpp`, `java`. This copies the
standard Makefile, container and CI files, a `.gitignore`, `AGENTS.md` and
`CLAUDE.md`, the requirements file, the alignment test and the task tool. It
never overwrites an existing file. It runs `git init` if the folder is not a
repository yet, and makes no commit. Commit the first setup yourself.

If git is not installed, the command prints how to install it. Ask the user to
install git, then run `git init` in the project.

## A folder of projects

`make -C <plugin folder> workspace PROJECTS=<folder>` writes `docs/` at the
folder's root, with an index, a per-project folder and notes. It also writes a
VS Code workspace file and `AGENTS.md`/`CLAUDE.md`. Run `make navigator` to
refresh the index after repos change. The repos themselves are not changed.

## After setup

- Run `make check` to confirm the project passes. A new project is expected to
  fail until its requirements, tests and CI placeholders are filled in.
- Fill in `docs/requirements.md` before writing features.
- Commit `AGENTS.md`, `CLAUDE.md`, `docs/` and the task folders, so the whole team
  and every agent see them.

## Rules

- Never overwrite a file the user has edited. Report what was kept.
- Do not turn a folder of repos into a repository unless the user asks.
