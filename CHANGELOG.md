# Changelog

All notable changes. Versions follow semantic versioning; see `scripts/release.py`.

## [Unreleased]

- Coding standards, the Python skill and the review checklist now say to use an
  existing library function instead of a hand-written helper, to keep your own
  only with a stated reason, and to check for empty input before a mean or
  other reduction.

- Code review checklist now covers refactors: find every use of what was
  replaced, check loaded data matches its types, run the real entry points, and
  run the formatter check after editor edits.

- Coding standards and the Python skill now say to define a fixed set of values
  once, as a `StrEnum`, not as a `Literal` type plus a matching tuple. The
  Python skill covers repr, JSON, loading, membership tests, finishing a
  migration and when `Literal` is fine.

## [0.1.0] - 2026-11-07

- Added git-workflow, versioning-release and code-comments skills, based on Conventional
  Commits, trunk-based branching and Keep a Changelog.
- Added templates: `.gitattributes`, `.gitmessage` (commit template), a pull request
  template and a changelog. `init-project` copies them and sets the commit template.
- Fuller `.gitignore` for build output, caches, secrets and editor files.
- Installs copy the plugin into each client's own folder instead of linking to the
  project, so removing the project folder does not break them. Uninstall removes
  only what the installer created.

- Removed Gemini CLI support: its manifest, GEMINI.md, installer and install-all step.
  Antigravity is the replacement; its plugin is linked with `make install-antigravity`.

- Added skills for the feature workflow, task tracking, standing decisions,
  project alignment and project setup. Added `make decisions-sync`.

- Task tool (`make task-new`, `task-move`, `tasks`, `decide`) keeps a UTC log with
  the person who made each change, and lists rejections and decisions in a generated
  block of AGENTS.md so agents do not re-propose them. `init-project` runs `git init`
  when needed and asks you to install git if it is missing.

- Projects created with `make init-project` get `tests/alignment/`, a test that
  checks the project against the guidelines (README, standard targets, ignore
  rules, no committed secrets, lock files, container and CI hygiene, tests exist).
  `make check` runs it.
- Projects also get `docs/requirements.md`. The alignment test requires every
  requirement to have a test that names its ID (REQ-001), rejects tests that name
  unknown IDs, and checks that relative links in `docs/` point at real files.

- Added the Docker, Compose, project-make and refresh-practices skills.
- Added language Makefiles, Dockerfile, Compose and ignore templates.
- Removed every hard-coded version number from skills. Versions are looked up
  live (`make versions`) from the sources each skill names.
- Added `make init-project` and `make versions`.
- Added the test suite (`make test`, part of `make check`) that keeps manifests,
  skills, templates, generators and rule copies aligned.
- Initial language, repo-shape, architecture and CI/CD guidance.
