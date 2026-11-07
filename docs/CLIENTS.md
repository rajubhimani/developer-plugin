# Client compatibility

This plugin ships one set of skills and rules. Each client reads them through its
own manifest. The table lists what each client needs and how it was checked.

| Client | Manifest | Skills | Rules | Hooks | Install | Status |
|---|---|---|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `skills/` | `AGENTS.md` via `CLAUDE.md` | `hooks/hooks.json` | `make install-claude` | Installed from its own copy |
| Codex | `plugin.json` | `skills/` | `AGENTS.md` | not used | `make install-codex` | Installed and enabled from its own copy |
| GitHub Copilot CLI | `plugin.json` (Agent Plugins 1.0) | `skills/` | not generated | not used | `make install-copilot` | Installed from GitHub; reinstall after the branch is merged |
| Antigravity | `plugin.json` | `skills/` | `rules/AGENTS.md` | `hooks.json` at root | `make install-antigravity` | Copied; shows in the app's plugin list |

## Where each client keeps its copy

Each install copies the plugin into the client's own folder, so deleting the
project folder does not break it. Re-run the install to pick up changes.

- Claude Code: `~/.claude/plugins/marketplaces/developer-plugin-local`
- Codex: `~/.codex/marketplaces/developer-plugin-local` (then `~/.codex/plugins/cache`)
- Antigravity: `~/.gemini/config/plugins/developer-plugin`
- Copilot CLI: `~/.copilot/installed-plugins` (copied from the git remote)

## Notes

- Claude Code runs the session hook from `hooks/hooks.json`. Antigravity expects
  `hooks.json` at the plugin root, so the root file uses its named-hook format.
- Copilot's direct installs from a git URL are deprecated. A marketplace will be
  needed eventually.
- Copilot installs the default branch, so changes reach it only after they are merged.
- Gemini CLI was removed: Antigravity replaces it for individual accounts.
