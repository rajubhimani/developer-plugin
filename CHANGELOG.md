# Changelog

All notable changes. Versions follow semantic versioning; see `scripts/release.py`.

## [Unreleased]

- Leaner prompts. Skill and agent descriptions load into every session, so 52 of them are
  shorter (what each covers and its "Use when" trigger are kept; the enumerated lists are
  gone). Claude Code's own figure for the plugin's always-on cost fell from about 5,970 to
  about 5,110 tokens. `ai-assisted-development` gains "Spend tokens wisely" (clear between
  tasks, keep always-loaded text small and stable for prompt caching, turn off unused tools,
  point instead of paste, match model and effort to the job, cap automated runs) and
  `agent-handoff` gains a note on cheap dispatch. `make check` now fails on a description over
  300 characters or a skill body over 500 lines, and `make token-cost` prints an estimate.

- Shareable Claude Code install and a Claude installer that can be run at any time. Anyone can
  install with `/plugin install developer-plugin --marketplace rajubhimani/developer-plugin`;
  the marketplace is now named `developer-plugin` (was `developer-plugin-local`) with an owner,
  a description, and an author, homepage and repository on the plugin, and `make check`
  enforces them. `scripts/install.py claude` keeps its copy in `~/.developer-plugin/claude`
  instead of inside Claude's own folders (Claude deletes a removed marketplace's folder, which
  made a re-install fail on the first try), never removes a marketplace except to change its
  source, reinstalls the plugin so a same-version change is picked up, migrates an earlier
  install, and checks at the end that the plugin is enabled at the expected version. Tests run
  the installer against a stand-in `claude` that deletes a removed marketplace's folder.

- Maintained libraries and no deprecated code, as standing rules. The core standards gain
  "Maintained code" (rules 23 to 25): choose maintained libraries and replace one that stops
  being maintained; replace a deprecated API, option or dependency when you find it, as its
  own commit with the tests green, and say what was replaced. The builder agent may fix a
  deprecation outside its task as its own commit (the one exception to "note, do not fix");
  the code reviewer flags one the change leaves. The generated projects make deprecations
  fail: Python (`reportDeprecated` and deprecation warnings as errors), TypeScript
  (`@typescript-eslint/no-deprecated`), Java and C and C++ (`-Xlint:all` or `-Werror`);
  Rust (`clippy -D warnings`) and Go (`golangci-lint`) already did. Applying the rule to the
  plugin's own templates replaced the deprecated `tseslint.config()` helper, the deprecated
  `spring-boot-starter-web` name and `httpx`-based Starlette test clients.
- New project kinds. Java (Gradle, Kotlin DSL, version catalog): library, cli, and a Spring
  Boot service with layers, problem details, graceful shutdown and health probes. C and
  C++ (CMake presets): library and executable, built with warnings as errors and sanitizers.
  Go monorepo (`go.work`). The Python webapp gains a SQLAlchemy adapter, Alembic migrations
  that run as a job with only the database URL, and a readiness check that pings the
  database. `make structure-check` learns the Go workspace, Java layer and CMake rules.

- Project kinds. `make init-project` now asks what the project is (once, in a terminal,
  or through `KIND=`, `NAME=`, `MEMBERS=`) and creates the layout that fits it, recording
  the answer in `.developer-plugin/project.json`. Python: library (src layout, public
  API, typed marker, publish workflow with trusted publishing), webapp (layered FastAPI
  service with a composition root, problem-details errors, health routes and the
  container files), cli, and a uv-workspace monorepo of apps and packages. TypeScript:
  webapp, library, ui and a pnpm-workspace monorepo (`apps/web`, `packages/ui`,
  `utils`, `config`). Go: service, library, cli. Rust: library, binary, workspace.
  `make structure-check` (a self-contained script copied into each project and run by
  `make check`) reads the record and reports missing required files, flat layouts, a
  domain that imports a framework, an app imported by a package, a package that
  imports an app, siblings not linked through the workspace, and unfilled placeholders.
  In an existing project only safe files are added and no code is moved. New skill
  `project-structure`; `project-setup` now says to ask first. Java, C and C++ keep the
  generic layout. The shared Python Dockerfile now starts the app through a factory.

- Python projects now get a typed settings class and a check that keeps names in
  step. `make init-project ... LANG=python` copies a uv multi-stage Dockerfile, a
  Compose stack, `.env.example`, a `.dockerignore` and `src/app/settings.py`
  (pydantic-settings, credentials as `SecretStr`, an optional secrets directory),
  never over an existing file, and adds `make check-env` to `make check`.
  `scripts/check_env.py` (standard library only) fails when the Settings fields,
  `.env.example` and the cluster manifests disagree, when a required setting is
  never supplied to the cluster, or when a credential is given as plain config.

- Added a `kubernetes` skill (configuration through ConfigMap and Secret, probes,
  resources, graceful shutdown, security context, scaling, jobs and migrations,
  Kustomize or Helm, rollback) with an annotated manifest set, a `.env` to cluster
  config guide and a Kustomize layout. Added language references: every `lang-*`
  skill now has `references/idioms.md` for that language's errors, concurrency,
  configuration, logging, testing, security and container image. `lang-python` gains
  a uv multi-stage Dockerfile with layer and cache rules, a Compose stack, `.env`
  and `.dockerignore` templates and a Docker, Compose and Kubernetes guide. The
  `docker` and `compose` skills gain layer-caching and `.env` rules. Tests check
  that every reference link in a skill resolves.

- Added sixteen skills from a broad review of current developer practice:
  `design-patterns`, `domain-modeling`, `error-handling`, `resilience`,
  `observability`, `database-migrations`, `refactoring`, `api-design`,
  `performance`, `dependency-management`, `secrets-and-config`, `accessibility`,
  `concurrency`, `architecture-decisions`, `delivery-practices` and
  `ai-assisted-development`. They state stable principles and send tool and
  number choices to a lookup, so they stay valid as tools change. `testing-strategy`
  gained property-based, mutation, contract and flaky-test guidance. The agents
  now list the skills that fit their role.

- Installs now record a manifest (version, source and a hash per file) in each
  copy and report "N added, M updated, K unchanged, J removed". New: `--dry-run`
  to preview, `make check-install` to report drift read-only, and a stop before
  a downgrade or major step unless `--confirm-update` is given. The copy is built
  beside the old one and swapped in, so a crash leaves a whole copy. Older
  installs without a manifest are replaced on the next install. A working-tree
  install copies only files git tracks or would not ignore, and never symlinks,
  so untracked secrets are not shipped; a folder this installer did not make is
  not replaced without confirmation; a refused step exits non-zero.

- Added twelve role-named Claude Code subagents in `agents/`: `researcher`,
  `requirements-analyst`, `architect`, `test-designer`, `planner`, `test-writer`,
  `builder`, `docs-writer`, `code-reviewer`, `security-reviewer`,
  `deploy-reviewer` and `debugger`. Reviewers and the debugger are read-only. A
  new `agent-handoff` skill holds the order, the brief, the report, how to
  verify a report and how to route findings. Validation and tests check each
  agent's front matter, the skills it names, its tool grants and that every
  role exists.

- Added generic skills adapted from a study of another team's workflow plugin:
  `untrusted-input`, `shell-hygiene`, `writing-style`, `testing-strategy`,
  `security-review`, `debug-failure` and `change-triage`. The review checklist
  now covers test honesty, security, untrusted text and evidence-based blocking
  findings. The git workflow now covers pull request descriptions written for
  the person who decides, rollback lines, and keeping probes out of the shared
  working tree.

- Coding standards and the Python skill now say to call your own functions and
  classes by keyword (`Token(id=1, form=word)`), with the exceptions for single
  obvious arguments and positional-only library functions, and to mark
  must-name parameters keyword-only with `*`. Later rules are renumbered.

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
