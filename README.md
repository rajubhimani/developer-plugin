# developer-plugin

One source tree, four tools. Skills live once in `skills/`; each tool reads
them through its own manifest.

| Tool | Manifest used | Skills | Context / other |
|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `skills/` | — |
| Codex | `plugin.json` (root) | `skills/` | — |
| GitHub Copilot | `plugin.json` (root) | `skills/` | `com.github.copilot/` for Copilot-only parts |
| Gemini CLI | `gemini-extension.json` | `skills/` | `GEMINI.md` |

## Layout

```text
plugin.json                  Copilot + Codex manifest (Agent Plugins 1.0)
.claude-plugin/plugin.json   Claude Code manifest
gemini-extension.json        Gemini CLI manifest
GEMINI.md                    Gemini context file
skills/<name>/SKILL.md       shared skills (read by all four tools)
```

Keep the `version` the same in all three manifests. `scripts/validate.py` checks
that and the skill frontmatter.

## Rules

`rules/coding-standards.md` is the only place the coding rules are edited.
`make sync-rules` generates the copies each tool reads:

- `skills/coding-standards/SKILL.md` (Claude Code, Codex, Copilot)
- `GEMINI.md` (Gemini CLI, always loaded)

`make validate` fails if a copy is out of date.

Skills are chosen by their description, so they load when relevant. Gemini's
`GEMINI.md` is always loaded. Copilot's rules folder (`com.github.copilot/rules/`)
is not generated yet; its file format is unverified.

## Adding a skill

Create `skills/<kebab-case-name>/SKILL.md` with `name` (same as the folder) and
`description` in the frontmatter. Invalid names are silently skipped by Copilot,
so run the validator.

## Testing locally

- **Claude Code:** `/plugin` and add this folder as a local marketplace, or use
  the plugin-dir flag if your version supports it (`claude --help`).
- **Codex:** add this folder under a local marketplace (`.agents/plugins/marketplace.json`)
  or run `codex plugin marketplace add <dir>`, then enable it in `.codex/config.toml`.
- **GitHub Copilot (VS Code):** enable `chat.plugins.enabled`, then
  "Chat: Install Plugin from Source" and pick this folder.
- **Gemini CLI:** `gemini extensions link /Users/raju/Projects/developer-plugin`,
  then restart the CLI.

Gemini CLI was reported as replaced by Antigravity CLI on 18 June 2026. Check
which one you use before relying on the Gemini install steps.
