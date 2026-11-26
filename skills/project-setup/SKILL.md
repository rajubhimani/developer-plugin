---
name: project-setup
description: Set up a new or existing project, or a folder of projects, with this plugin's files, git, make targets, docs and task tracking. Use when starting a project, adding the plugin's structure to a repo, or setting up docs for a folder of repos.
verified: 2026-11-26
---

# Project setup

## One project

First find out what the project is. If the folder has no
`.developer-plugin/project.json`, ask the user what they are building (library, web app or
service, command line tool, monorepo) and follow `project-structure`; it picks the layout
and records the answer so nobody is asked twice. If the folder already holds code, also ask
whether to follow best practice or keep the project's own structure, and honour the answer.

`make -C <plugin folder> init-project REPO=<project folder> LANG=<language> KIND=<kind> NAME=<name>`

Languages: `python`, `go`, `rust`, `node`, `c`, `cpp`, `java`. Every language has kinds (see
`project-structure`); without a kind and without a terminal the generic layout is used. A monorepo also takes `MEMBERS=name:kind,name:kind`. In a
terminal, leaving `KIND` out asks the questions.

This copies the kind's layout (for example `src/`, the public API and the tests for a
library), then the standard Makefile, container and CI files, a `.gitignore`, `AGENTS.md`
and `CLAUDE.md`, the requirements file, the alignment test, the task tool and the layout
check (`make structure-check`). It never overwrites an existing file. In a folder that
already holds a project it records the kind and the structure choice (`STRUCTURE=best-practice`
or `own`, default `own`) and adds only safe files; it never creates source files or moves code.
With `own` it writes `docs/project-structure.md`, the note every agent follows; with
`best-practice` it writes `docs/structure-plan.md`. It runs `git init` if the folder is not a repository yet, and
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

## Bring a project up to date

When the plugin has changed, run `make init-project REPO=<folder> LANG=<language> UPDATE=1`
(`DRY=1` first to look). It refreshes only files nobody edited, keeps and diffs the ones the
person edited, creates missing ones, and deletes nothing. It needs a clean git tree: commit or
stash first, so the update is its own change.

## Permissions

The setup adds `.claude/settings.example.json`: a short allow list (`make check`, `make test`,
`make lint`, read-only git) and a deny list, so routine commands stop asking. To use it, copy it
to `.claude/settings.local.json` (untracked) or merge it into `.claude/settings.json`. It leaves
out any stdin interpreter (`python -`, `bash -c`) and container exec or run, on purpose: an agent
reads text from strangers (issues, web pages), and those commands turn a planted instruction into
data leaving the machine. Add a project command only as a fixed command, never a `*` wildcard.

The same file wires a git guard (`scripts/block_dangerous_git.py`) as a hook. It blocks force and
delete pushes, `reset --hard`, `clean -f`, `branch -D`, `checkout .`, `restore .` and `stash drop`
before they run, reading the command as a shell would, so `git -C repo push --force` is caught and
`echo "git push -f"` is not. A plain push or commit is allowed.

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
