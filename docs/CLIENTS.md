# Client compatibility

This plugin ships one set of skills and rules. Each client reads them through its
own manifest. The table lists what each client needs and how it was checked.

| Client | Manifest | Skills | Rules | Hooks | Install | Status |
|---|---|---|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `skills/` | `AGENTS.md` via `CLAUDE.md` | `hooks/hooks.json` | `make install-claude` | Installed from its own copy |
| Codex | `plugin.json` | `skills/` | `AGENTS.md` | not used | `make install-codex` | Installed and enabled from its own copy |
| GitHub Copilot CLI | `plugin.json` (Agent Plugins 1.0) | `skills/` | not generated | not used | `make install-copilot` | Installed from GitHub; reinstall after the branch is merged |
| Antigravity | `plugin.json` | `skills/` | `rules/AGENTS.md` | `hooks.json` at root | `make install-antigravity` | Copied; shows in the app's plugin list |

## Agents

`agents/*.md` holds twelve role-named subagents, each preloading the skills it
follows (see the README for the list). Only Claude Code reads them
today. Codex, Copilot and Antigravity use their own agent formats, which are
not generated or verified yet, so they still get the skills alone.

Codex agents were tried and not adopted. The format is simple (one TOML file per agent in
`.codex/agents/` with `name`, `description` and `developer_instructions`, and names limited to
lowercase letters, digits and underscores), and the files generated from `agents/*.md` were valid.
But a real Codex session (current release, trusted project) reported that no selectable `agent_type` is
exposed, so the agents could not be spawned; this matches an open Codex issue about custom agents
not reaching tool-backed sessions. Revisit when Codex fixes it, by re-running that listing test
before writing any installer for it.

## Where each client keeps its copy

Each install copies the plugin into the client's own folder, so deleting the
project folder does not break it. Re-run the install to pick up changes.

- Claude Code: `~/.developer-plugin/claude` (registered as the `developer-plugin` marketplace; Claude
  keeps its own cache under `~/.claude/plugins/cache`). From GitHub there is no local copy to manage.
- Codex: `~/.codex/marketplaces/developer-plugin-local` (then `~/.codex/plugins/cache`)
- Antigravity: `~/.gemini/config/plugins/developer-plugin`
- Copilot CLI: `~/.copilot/installed-plugins` (copied from the git remote)

## Checking an install

`make check-install` compares each copy against this checkout (version, source
folder and file hashes) and reports stale, edited, missing or no-longer-shipped
files. Copilot installs from the git remote and is not checked. Copies made
before the manifest existed report as unreadable until you re-run their installer.

## Notes

- Claude Code runs the session hook from `hooks/hooks.json`. Antigravity expects
  `hooks.json` at the plugin root, so the root file uses its named-hook format.
- Copilot's direct installs from a git URL are deprecated. A marketplace will be
  needed eventually.
- Copilot installs the default branch, so changes reach it only after they are merged.
- Gemini CLI was removed: Antigravity replaces it for individual accounts.
