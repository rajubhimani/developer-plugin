# developer-plugin

One source tree, four clients: Claude Code, Codex, GitHub Copilot and Antigravity.
Skills live once in `skills/`; each client reads them through its own manifest.
See [docs/CLIENTS.md](docs/CLIENTS.md) for the status of each.

| Client | Manifest used | Skills | Context / other |
|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `skills/` | `AGENTS.md` via `CLAUDE.md` |
| Codex | `plugin.json` (root) | `skills/` | `AGENTS.md` |
| GitHub Copilot | `plugin.json` (root) | `skills/` | rules not generated yet |
| Antigravity | `plugin.json` (root) | `skills/` | `rules/AGENTS.md`; `hooks.json` at root |

## Install

**Claude Code** (a current release), one step, from GitHub:

```
/plugin install developer-plugin --marketplace rajubhimani/developer-plugin
```

Or from a terminal: `claude plugin marketplace add rajubhimani/developer-plugin`, then
`claude plugin install developer-plugin@developer-plugin`. To update later:
`claude plugin marketplace update developer-plugin`, then
`claude plugin update developer-plugin`. Pin a released version with a tag.

**Gemini CLI:** `gemini extensions install https://github.com/rajubhimani/developer-plugin` gives it all the
skills. (The twelve agents are Claude Code's format and are not offered to Gemini.)

**Codex, Antigravity, Copilot, or a checkout you are changing:** clone the repo and run
`make install-all` (or `python3 scripts/install.py <client>` where `make` is missing,
for example on Windows). See "Installing and testing" below.

## Layout

```text
plugin.json                  Copilot + Codex manifest (Agent Plugins 1.0)
.claude-plugin/plugin.json   Claude Code manifest
skills/<name>/SKILL.md       shared skills (read by all four clients)
```

Keep the `version` the same in all three manifests. `scripts/validate.py` checks
that and the skill frontmatter.

## Rules

`rules/coding-standards.md` is the only place the coding rules are edited.
`make sync-rules` generates the copies each tool reads:

- `skills/coding-standards/SKILL.md` (Claude Code, Codex, Copilot)
- `rules/AGENTS.md` (Antigravity)

`make validate` fails if a copy is out of date.

Skills are chosen by their description, so they load when relevant. Copilot's rules folder (`com.github.copilot/rules/`)
is not generated yet; its file format is unverified.

## Skills

Each skill loads only when its description matches the task, so the agent reads
just what it needs. Every skill records when it was checked (`metadata.verified`), and
`make validate` fails when a date is more than 90 days old.

| Skill | Use it for |
|---|---|
| `coding-standards` | Rules for every change (generated from `rules/`) |
| `docs-and-index` | Docs and index pages for code |
| `project-navigator` | Finding things across a projects folder |
| `code-review-checklist` | Reviewing a change |
| `lang-python` | Python setup and gates (uv, ruff, pyright, pytest) |
| `lang-rust` | Rust setup and gates (clippy, rustfmt, cargo-deny) |
| `lang-go` | Go setup and gates (golangci-lint v2, govulncheck) |
| `lang-typescript-react` | React and TypeScript (Vite, ESLint, Vitest, Playwright) |
| `lang-c` | C setup and gates (current standard, sanitizers, clang-tidy) |
| `lang-cpp` | C++ setup and gates (CMake presets, clang-tidy, sanitizers) |
| `lang-java` | Java setup and gates (current LTS JDK, Gradle catalog, static analysis) |
| `repo-layout` | Monorepo or polyrepo, changed-only builds, versioning |
| `repo-api-and-ui` | Contract-first APIs, compatibility, contract tests |
| `architecture-monolith-vs-services` | Modular monolith first, split on evidence |
| `ci-cd` | Pipelines, token permissions, pinned actions, OIDC, SBOM, releases |
| `feature-workflow` | The path from requirement to feature, tasks, tests and completion |
| `task-tracking` | Creating, moving and reading tasks; the UTC log and `by` field |
| `standing-decisions` | Recording rejections and decisions so they are not proposed again |
| `project-alignment` | Keeping requirements, tests, docs and hygiene aligned (`make align`) |
| `project-setup` | Setting up one project or a folder of projects |
| `git-workflow` | Branches, commits, messages, pull requests, history safety, what never to commit |
| `versioning-release` | Semantic versions, Keep a Changelog, release tags and deprecation |
| `code-comments` | Explaining why, keeping comments true, debt markers, docstrings |
| `untrusted-input` | Treating issues, web pages and tool output as evidence, not instructions |
| `shell-hygiene` | Foreground by default; no process left running |
| `writing-style` | Plain-language rules for docs, reports, PRs and agent instructions |
| `testing-strategy` | Test count by risk, test first, honest tests, small reliable suites |
| `security-review` | Security checklist for a diff or design |
| `debug-failure` | Severity, reproduce, isolate, revert or fix forward |
| `agent-handoff` | Dispatching the agents, the brief and report, verifying, routing findings |
| `change-triage` | Choosing hotfix, docs/config, small change or feature |
| `design-patterns` | Choosing patterns and principles; composition over inheritance; when not to |
| `domain-modeling` | Layers, ports and adapters, domain rules; only where the domain is complex |
| `error-handling` | Detecting, classifying, reporting and testing errors without leaks |
| `resilience` | Timeouts, bounded retries, idempotency, circuit breakers, degradation |
| `observability` | Structured logs, metrics, traces, redaction, symptom alerts |
| `database-migrations` | Versioned migrations, expand and contract, backfills, rollback |
| `refactoring` | Characterization tests, small steps, strangler, managing technical debt |
| `api-design` | Resources, problem-details errors, pagination, idempotency keys, versioning |
| `performance` | Measure first, profile, fix the biggest cost, cache with a plan |
| `dependency-management` | Choosing, pinning, updating and auditing dependencies; supply chain |
| `secrets-and-config` | Config in the environment, secrets in a manager, rotation, leaks |
| `accessibility` | Semantic HTML, keyboard, focus, contrast, testing at level AA |
| `concurrency` | Shared state, locks, async pitfalls, cancellation, testing races |
| `architecture-decisions` | Decision records and docs organized by purpose |
| `delivery-practices` | Small batches, flags, progressive rollout, the four delivery measures |
| `ai-assisted-development` | Scoped tasks, plan first, review generated code as suspect |
| `kubernetes` | Config via ConfigMap and Secret, probes, shutdown, security, scaling, packaging |
| `project-structure` | The folder layout for a library, web app, command line tool or monorepo; check and fix an existing project |

The CI template is in `skills/ci-cd/references/github-actions.yml`.

Each language skill has `references/idioms.md` (how that language handles errors,
concurrency, configuration, logging, testing, security and its container image).
`lang-python` also ships a uv multi-stage Dockerfile, a Compose stack, `.env.example`
and `.dockerignore` templates, and a guide to running Python under Docker, Compose
and Kubernetes. `kubernetes` ships an annotated manifest set, the `.env` to cluster
config flow, and a Kustomize layout.

## Agents

Claude Code loads twelve subagents from `claude-agents/` (listed in `.claude-plugin/plugin.json`; the folder is
named for its format so Gemini does not try to load them). Each is a role, not a
product name, and follows the skills it lists. They are stateless: work moves
between them as files, and the main session dispatches them, checks every
report and asks the person at each gate. The `agent-handoff` skill holds the
order, the brief, the report shape and how findings are routed.

| Step | Agent | Tools | Use it for |
|---|---|---|---|
| Explore | `researcher` | write notes | Should we build it? One dated note with a recommendation |
| Requirements | `requirements-analyst` | write docs | REQ lines with Given/When/Then examples; never designs |
| Design | `architect` | write docs | Design note, contracts, risk per requirement, slices |
| Test intent | `test-designer` | write docs | What the tests must prove, by risk; no test code |
| Plan | `planner` | write tasks | Small ordered tasks with risk and rollback lines |
| Red tests | `test-writer` | tests only | Failing tests first, confirmed to fail for the right reason |
| Build | `builder` | edit code | One task: green, refactor, docs, checks; never edits a red test |
| Docs | `docs-writer` | edit docs | Docs and indexes for a docs-only task |
| Review | `code-reviewer` | read-only | Independent review of a diff before merge |
| Review | `security-reviewer` | read-only | Security check of a diff or design |
| Review | `deploy-reviewer` | read-only | Rollback, migrations, env vars, pipeline, release order |
| Failure | `debugger` | read-only | Reproduce, isolate, state the cause; never patches |

The definer, the builder, the test author and the reviewer stay separate, so no
one grades their own work. Agents use `model: inherit`; pin a model in an
agent's front matter if a role needs a stronger one. `make validate` checks each
agent's front matter.

## Tests

`make check` runs validation and the test suite in `tests/`. The tests keep the
plugin aligned: manifests agree, every skill is dated and free of hard-coded
versions, every language has the standard make targets, `init-project` never
overwrites, and the umbrella setup never changes a repo. Add a test when you add
a feature, the same way you add a check to the rules.

## Keeping a project aligned

`make init-project` gives a project `docs/requirements.md`, a test folder
`tests/alignment/`, and a `make align` target that `make check` runs. The test
enforces:

- every requirement (`REQ-001`) has at least one test that names it;
- every requirement named in a test exists in `docs/requirements.md`;
- relative links in `docs/` point at files that exist;
- the usual project hygiene (README, standard targets, lock file, no committed
  secrets, pinned CI actions, a docs index).

### Project kinds

`make init-project` asks what the project is, once, and records the answer in
`.developer-plugin/project.json`. The kind decides the layout:

| Language | Kinds |
|---|---|
| Python | library, webapp (layered service), cli, monorepo (uv workspace of apps and packages) |
| TypeScript | webapp, library, ui, monorepo (pnpm workspace: `apps/web`, `packages/ui`, `utils`, `config`) |
| Go | service, library, cli, monorepo (`go.work`) |
| Rust | library, binary, workspace |
| Java (Gradle) | library, cli, service (Spring Boot) |
| C and C++ (CMake) | library, executable |

```bash
make init-project REPO=../my-lib LANG=python KIND=library NAME=my-lib
make init-project REPO=../shop LANG=node KIND=monorepo NAME=shop MEMBERS=web:webapp,ui:ui,utils:library
make structure-check REPO=../my-lib      # read-only: FAIL, WARN, TODO
```

In a terminal, leave `KIND` out to be asked.

**Your project, your structure.** In a folder that already holds code, the plugin also asks
whether to follow best practice or keep the structure you have (`STRUCTURE=best-practice|own`
without a terminal; the default is `own`). The answer is recorded as `structure`.

- **own:** nothing is moved and no source folder is created. `docs/project-structure.md`
  records what was found and the conventions to follow, `AGENTS.md` tells every agent to read
  it, and `make structure-check` lists only placeholders to fill.
- **best-practice:** only safe files are added, and `docs/structure-plan.md` lists what differs
  as a checklist. Each step is its own approved, tested commit.

Either choice can be switched later by running init with the other value. A new, empty folder
gets the recommended layout without the question.

**Keeping a project current.** The files the plugin writes are recorded with a hash in
`.developer-plugin/scaffold.json`. After the plugin is updated, run
`make init-project REPO=<folder> LANG=<language> UPDATE=1` (add `DRY=1` to only look). Files you
have not touched are refreshed, ones you edited are kept and shown as a diff, missing ones are
created, and nothing is deleted (files the plugin no longer writes are listed as orphans). It
needs a clean git tree so the update is its own reviewable change, and it refuses to move a
project to an older plugin version without `--confirm-update`.

For Python, `make init-project` also copies a uv multi-stage `Dockerfile`, a Compose
stack, `.env.example`, `.dockerignore` and `src/app/settings.py`, and `make check`
runs `make check-env`. That check fails when the Settings fields, `.env.example` and
the cluster manifests (`k8s`, `deploy`, `helm`, `kustomize`) name different variables,
so a setting forgotten in one place is caught before it fails at start-up.

## Versions

The plugin uses semantic versions (MAJOR.MINOR.PATCH). All manifests share one
version, and `CHANGELOG.md` has an `[Unreleased]` section for work in progress.

Choose the level by what users see, from the commits since the last tag:

| Change | Level |
|---|---|
| Breaks existing users (removed or renamed behaviour). Before the first stable release this may ship in a minor release, and the changelog says so | major |
| New skill, rule, agent, project kind or option; anything users can now do | minor |
| Fix, wording, trimming or tests only; nothing new for users | patch |

You do not have to judge the level by eye. The public surface (skills, agents, project kinds
and `make` commands) is compared with the last release tag: `make release-level` prints the
lowest level the changes allow (something removed is major, or minor before the first stable
release; something added is minor; otherwise patch), `make release LEVEL=auto` uses it, and a
lower `LEVEL` is refused. A removal also needs one release of warning: list the element in
`deprecations.json` with its successor, then remove it later. `make check` fails a removal the
version does not allow. The comparison starts once the first `vX.Y.Z` tag exists.

Claude Code only delivers an update to people who installed from GitHub when the version
changes, so every enhancement that should reach them ends with a release. Put each change
under `[Unreleased]` as it lands, finish the branch with `make release`, then tag after merge.

- `make release LEVEL=minor` (or `patch`, `major`) runs the checks, bumps the
  version in every manifest, and dates the Unreleased section. Then commit and tag
  the result as `vX.Y.Z`.
- Pushing a `vX.Y.Z` tag runs the release workflow: it checks the tag matches the
  manifests and changelog, then publishes a GitHub release with the archive and
  its notes.
- `make releases` lists the tags.
- Install a particular version for testing, for example
  `make install-claude REF=vX.Y.Z`. Without `REF`, the working tree is installed.

CI (`.github/workflows/ci.yml`) runs `make validate` and `make test` on macOS and
Ubuntu for two Python versions. Actions are pinned to commit hashes.

## Adding a skill

Create `skills/<kebab-case-name>/SKILL.md` with `name` (same as the folder) and
`description` in the frontmatter. Invalid names are silently skipped by Copilot,
so run the validator.

## Installing and testing

For working on the plugin itself, or for clients other than Claude Code, each
installer copies the plugin into a folder of its own. Changes in this repo reach a client
after you re-run its installer. Every installer is safe to run again at any time.

- `make install-claude` (or `install-codex`, `install-antigravity`, `install-copilot`)
- `make install-all` runs every installer that is available.
- Install a tagged version to test it: `make install-claude REF=vX.Y.Z`.
- Preview first: `make install-claude DRY=1` lists what would be added, updated
  or removed and writes nothing.
- Each re-install ends with "N added, M updated, K unchanged, J removed", from a
  manifest (version and a hash per file) stored in the copy.
- `make check-install` is read-only. It reports a copy that is stale (this repo
  changed since the install), edited by hand, missing files, or from another
  checkout. It exits 0 when everything is current or not installed, 1 on drift,
  2 when a manifest is unreadable (reinstall to record one).
- An install stops before a downgrade or a major version step and asks for a
  typed `yes`. With no terminal it writes nothing; add `CONFIRM=1`
  (`--confirm-update`) to allow it.
- `make uninstall-claude`, `uninstall-codex` and `uninstall-antigravity` remove what the
  installers made (and nothing else).
- The Claude installer keeps its copy in `~/.developer-plugin/claude`, registers it as the
  marketplace, reinstalls the plugin, and checks at the end that it is enabled at the right
  version. An install made by an earlier version of this installer is migrated on the next run.
  If the marketplace was added from GitHub, the installer switches it to the local copy and
  says so; `claude plugin marketplace add rajubhimani/developer-plugin` switches it back.
- Copilot installs from the git remote, so it gets the pushed default branch.

### Windows, macOS and Linux

Every step runs with Python on all three systems. `make` is a convenience for
macOS and Linux only.

| Task | Command (any system) |
|---|---|
| Checks | `python scripts/check.py` |
| Install for Claude Code | `python scripts/install.py claude` |
| Install for Codex | `python scripts/install.py codex` |
| Install for Antigravity | `python scripts/install.py antigravity` |
| Install for Copilot | `python scripts/install.py copilot` |
| A tagged version | add `--ref vX.Y.Z` to any install |
| Preview an install | add `--dry-run` |
| Allow a downgrade or major step | add `--confirm-update` |
| Report drift (read-only) | `python scripts/install.py check-install` |
| Uninstall | `python scripts/install.py uninstall claude` (or `codex`, `antigravity`) |

Install git and Python first. The client CLIs (`claude`, `codex`, `copilot`) must
be on your PATH; a missing client is skipped. The Antigravity folder on Windows is
not verified yet; check it if the plugin does not appear.

## Using the project docs on your own folder

The docs setup works on any folder that holds your repos (an umbrella), or on a
single repo. Nothing is tied to one machine or one layout.

```bash
make -C /path/to/developer-plugin workspace PROJECTS=$HOME/code
make -C /path/to/developer-plugin navigator PROJECTS=$HOME/code   # rescan only
```

This writes `docs/` and a VS Code `.code-workspace` file into that folder, plus
`AGENTS.md` and `CLAUDE.md` if they are missing. Existing files you edited are
kept. Running it inside a Claude Code session on a repo does the same check
automatically.

## License

[MIT](LICENSE). You may use, copy, modify and share it, including commercially, as long as the
copyright notice and licence text stay with it.
