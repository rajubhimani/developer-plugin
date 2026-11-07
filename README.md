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
just what it needs. Every skill records when it was checked (`verified:`), and
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

The CI template is in `skills/ci-cd/references/github-actions.yml`.

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

## Versions

The plugin uses semantic versions (MAJOR.MINOR.PATCH). All manifests share one
version, and `CHANGELOG.md` has an `[Unreleased]` section for work in progress.

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

Each installer copies the plugin into the client's own folder. Changes in this
repo reach a client after you re-run its installer.

- `make install-claude` (or `install-codex`, `install-antigravity`, `install-copilot`)
- `make install-all` runs every installer that is available.
- Install a tagged version to test it: `make install-claude REF=vX.Y.Z`.
- `make uninstall-claude` and `make uninstall-antigravity` remove what the installers made.
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
