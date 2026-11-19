---
name: project-setup
description: Set up a new or existing project, or a folder of projects, with this plugin's standard files, git repository, make targets, docs and task tracking. Use when starting a project, adding the plugin's structure to a repo, or setting up docs for a folder that holds several repos.
verified: 2026-11-07
---

# Project setup

## One project

First find out what the project is. If the folder has no
`.developer-plugin/project.json`, ask the user what they are building (library, web app or
service, command line tool, monorepo) and follow `project-structure`; it picks the layout
and records the answer so nobody is asked twice.

`make -C <plugin folder> init-project REPO=<project folder> LANG=<language> KIND=<kind> NAME=<name>`

Languages: `python`, `go`, `rust`, `node`, `c`, `cpp`, `java`. Every language has kinds (see
`project-structure`); without a kind and without a terminal the generic layout is used. A monorepo also takes `MEMBERS=name:kind,name:kind`. In a
terminal, leaving `KIND` out asks the questions.

This copies the kind's layout (for example `src/`, the public API and the tests for a
library), then the standard Makefile, container and CI files, a `.gitignore`, `AGENTS.md`
and `CLAUDE.md`, the requirements file, the alignment test, the task tool and the layout
check (`make structure-check`). It never overwrites an existing file. In a folder that
already holds a project it records the kind and adds only safe files; it never creates
source files or moves code. It runs `git init` if the folder is not a repository yet, and
makes no commit. Commit the first setup yourself.

Replace every `<placeholder>` in the manifests from a current lookup (`make structure-check`
lists them), then run `make install` and `make check`.

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
- Ask what the project is before creating its layout; never guess a kind.
- Do not turn a folder of repos into a repository unless the user asks.
