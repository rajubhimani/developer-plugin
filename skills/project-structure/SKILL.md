---
name: project-structure
description: Choose and apply the folder layout that fits the project (library, web app or service, CLI, monorepo), asking once, and check an existing project's structure. Use when starting a project, restructuring, or asked whether a project follows best practice.
verified: 2026-11-19
---

# Project structure

A library, a web app, a command line tool and a monorepo need different folders,
files and rules. Ask what the project is, apply the matching layout, record the answer,
and check it later. The layouts and their reasons are in `references/layouts.md`.

## Ask first, once

If the folder has no `.developer-plugin/project.json`, ask the user before creating
anything. Use the question tool if you have it; one short question each:

1. **What are you building?** Pick one: library (other code imports it), web app or
   service (listens on a port, deployed), command line tool, or monorepo (several apps
   and packages in one repository).
2. **What is it called?** Lower-case words joined by hyphens.
3. **For a monorepo, which members?** Name and kind pairs, such as `web:webapp`,
   `ui:ui`, `utils:library`. Offer the default set for the language.

Then run (from the plugin folder):

```bash
make init-project REPO=<folder> LANG=<language> KIND=<kind> NAME=<name> [MEMBERS=a:kind,b:kind]
```

In a terminal the script asks the same questions itself. The answer is recorded in
`.developer-plugin/project.json`; do not ask again. To change a recorded kind, explain the
consequence, then delete that file and run again (existing files are kept).

## Kinds

| Language | Kinds | Monorepo members |
|---|---|---|
| python | library, webapp, cli, monorepo (uv workspace) | webapp, cli, library |
| node (TypeScript) | webapp, library, ui, monorepo (pnpm workspace) | webapp, library, ui, config |
| go | service, library, cli, monorepo (`go.work`) | service, cli, library |
| rust | library, binary, workspace | library, binary |
| java (Gradle) | library, cli, service (Spring Boot) | |
| c, cpp (CMake) | library, executable | |

## What each kind gets

- **library:** `src` layout, a public API that is listed and tested, a typed marker,
  a changelog, and a publish workflow that needs no stored token.
- **web app or service:** layers that import in one direction (routes, use cases,
  domain, adapters), a composition root, one error format, health routes with a real
  readiness check, settings read once, a storage adapter with migrations that run as a job,
  and the container and Compose files (see `lang-python`, `kubernetes`).
- **command line tool:** a thin entry point, logic in plain functions, documented exit
  codes, tests that call the entry function.
- **monorepo:** `apps/` that nothing depends on, `packages/` that apps share, one lock
  file, shared tool settings in the root, an owners file, and written dependency rules.

## Rules for every kind

1. Pick the layout that matches the product, not the one that looks most complete.
   Do not add layers or packages "for later" (see `domain-modeling`, `design-patterns`).
2. Entry points are thin; logic lives where tests reach it without a process.
3. Dependencies point one way. Write the rule down and have a check enforce it.
4. One lock file per workspace; shared tool settings in one place.
5. A public API is a list, not an accident: export on purpose, test it, version it.
6. Never leave placeholders in a manifest: replace each one from a current lookup
   (language release, license, repository), never from memory.
7. Use maintained libraries only, and make deprecations loud: every kind turns a
   deprecated call into a failing check (see `dependency-management`). Replace what the check
   finds with the documented replacement, as its own commit.

## Check and fix an existing project

1. Run `make structure-check REPO=<folder>` (or `make structure-check` inside a project
   made by the plugin). It is read-only and reports FAIL (broken layout), WARN (against
   advice) and TODO (placeholder to fill).
2. If the project has no record, the check says what it looks like. Confirm the kind with
   the user, then run `make init-project ... KIND=<kind>`. In a folder that already holds a
   project this records the kind and adds only safe files (docs, owners file, tests
   folder). It never creates source files and never moves or overwrites code.
3. Report the findings in the order: broken boundaries, missing required files, layout
   moves, warnings. Moving code (a flat layout to `src`, splitting a package) is a
   refactor: propose it, get approval, do it in small steps with tests green (see
   `refactoring`).
4. Re-run the check until FAIL is empty. Add `make structure-check` to the CI gate; the
   generated `make check` already runs it.

## Related

`project-setup` (the files every project gets), `repo-layout` (monorepo or polyrepo),
`lang-*` skills (tools per language), `architecture-decisions` (record the choice).
