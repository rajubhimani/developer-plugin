# Changelog

All notable changes. Versions follow semantic versioning; see `scripts/release.py`.

## [Unreleased]

- Frontmatter is now valid YAML for every reader. 31 of the 66 skill and agent files had a `description` with an
  unquoted colon (many from the earlier description trimming), which Claude Code and Gemini's skill loader accept
  but a strict YAML parser rejects. Every description is now a quoted string, the generator for the
  `coding-standards` skill writes it that way, and `make check` fails an unquoted one (and, where PyYAML is
  installed, parses every frontmatter strictly). After the change, 3 of 8 eval cases were re-run and passed
  9 of 9 (`git-workflow` 2 of 2 before a usage limit stopped the run); re-run `make evals` to cover the rest.

- Gemini CLI support. `gemini-extension.json` (versioned with the other manifests, which `make check` and
  `make release` keep in step) lets Gemini install the plugin from GitHub with `gemini extensions install`.
  Checked with Gemini itself: it validates, and all the skills load. Gemini also loads any `agents/` folder
  in an extension and rejected our Claude-format agents (`tools` as a string, a `skills` key), so the agent
  files moved from `agents/` to `claude-agents/` and `.claude-plugin/plugin.json` now lists them. Claude Code
  still finds all twelve (confirmed live) and Gemini reports no agent errors. `make check` fails if the list
  and the folder disagree, and the version-level check treats the move as the same agents, not twelve removals.

- Skill-triggering evals. `evals/` holds eight cases for `claude plugin eval`, each a realistic prompt with a
  grader that checks the right skill was loaded (debug-failure, kubernetes, dependency-management, git-workflow,
  testing-strategy, secrets-and-config, project-structure, docker). `make evals` runs them three times each (opt-in, about
  $3 on your own account); `make check` runs a free static check that each case is well formed and names a real skill.
  A control case with the wrong skill failed as it should. Against the current descriptions 40 of 41
  runs loaded the right skill, so triggering is probabilistic and a case passes at two of three runs.

- A git guard for agents. `scripts/block_dangerous_git.py` is a Claude Code hook that blocks force and
  delete pushes, `reset --hard`, `clean -f`, `branch -D`, `checkout .`, `restore .` and `stash drop`/`clear`
  before they run, and allows ordinary git. It reads the command with a shell tokenizer, so
  `git -C repo push --force` and `make test && git reset --hard` are caught while `echo "git push -f"` is not,
  and it is plain Python so it works on Windows. New projects get the script and the hook wiring in
  `.claude/settings.example.json`. Confirmed in a real session: a `git reset --hard` was blocked and the
  uncommitted change survived.

- A `handoff` skill: write a short note so a fresh session can continue the work (goal, state, decisions,
  where things are, how to check, next step), saved to the temp folder, never committed. It is manual-only
  (`disable-model-invocation`), and a fresh session was confirmed not to see it, so it adds nothing to the
  always-on cost. `make check` now also fails a skill file of 20,000 bytes or more, the point where Claude
  Code cuts a re-attached skill after compaction.

- Added the MIT licence (`LICENSE`, and `license` in both manifests, which `make check` now requires), so the
  plugin can be used and shared by others.

- Projects can now be brought up to date. New projects record a hash of every file the plugin wrote in
  `.developer-plugin/scaffold.json`, and `init_project.py --update` (`make init-project ... UPDATE=1`,
  `DRY=1` to look) refreshes only files nobody edited, keeps and diffs the ones you edited, creates missing
  ones and deletes nothing (files the plugin no longer writes are listed as orphans). It needs a clean git
  tree, refuses to move a project backwards without `--confirm-update`, and never touches the note or plan of
  an owner's own structure. Before this, a project forked from the templates on day one and never got
  improvements.

- A machine check for gamed tests. `scripts/check_tests_honest.py` (`make honest-tests`, also
  copied into new projects) fails when a branch adds a skip, disable, ignore or focus marker,
  removes assertions beyond those it adds, or deletes a test file. A deliberate skip carries
  `honest-ok: <reason>`. The builder runs it, the reviewer quotes it, and the testing skill says
  what it cannot see.
- New projects get `.claude/settings.example.json`: routine make targets and read-only git allowed,
  force push and `rm -rf` denied, and no stdin interpreter or container exec, so routine commands
  stop asking without opening a prompt-injection path.
- The code review checklist marks the items a command decides, and tells the reviewer to confirm a
  quoted result for the current commit instead of running the command again.
- Agents start small. Claude Code injects the full text of every skill in an agent's `skills` list, and
  ours preloaded 3 to 16 skills each. Each agent now preloads 2 or 3 and loads the rest on demand with
  the Skill tool (a Load on demand section says when). One dispatch of an agent used to cost about
  3,000 to 15,500 tokens and now costs about 1,400 to 3,000; across the 12 agents that is 23,400 tokens
  instead of about 89,600. `make check` fails on a missing skill name, a preload over 3,000 tokens, or
  a Load on demand section without the Skill tool.
- The version level is now derived, not guessed. `scripts/surface.py` lists what users can name
  (skills, agents, project kinds, make commands) and compares it with the last release tag:
  `make release-level` prints the lowest level the changes allow, `make release LEVEL=auto` uses
  it, and a lower level is refused. A removal needs a deprecation first (`deprecations.json`) or
  a major release (a minor one before 1.0); `make check` fails one that has neither. CI now
  fetches tags and history so the comparison can run.

## [0.2.0] - 2026-11-25

- Your project, your structure. In a folder that already holds code, `init_project.py` now asks
  once whether to follow best practice or keep the project's own structure (`--structure
  best-practice|own`; the default without a terminal is `own`, so an existing layout is never
  imposed). `own` records what was found and the conventions in `docs/project-structure.md`,
  points `AGENTS.md` at it, creates no source folders, and `make structure-check` stops
  enforcing a layout. `best-practice` writes `docs/structure-plan.md`, a checklist of what
  differs, to be done in approved, tested steps. The choice is recorded as `structure` and can
  be switched later. A new, empty folder still gets the recommended layout. The
  `project-structure` and `project-setup` skills tell agents to ask and to honour the answer.
  Existing projects initialised before this keep behaving as best practice until re-run.

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
