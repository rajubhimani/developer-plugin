# Decisions we measured and chose not to change

Each of these came from studying other open-source plugins. We tried or measured it and kept
things as they are. Reopen one only with new evidence.

## One plugin, not a core plus optional packs

Splitting into a core plugin and packs (infrastructure, languages, architecture, maintainers) is
how the largest marketplace we studied keeps its cost down. For us, a core-only install would
carry about 2,000 tokens always on instead of about 3,500, a saving of about 1,500 tokens per
session, under 1% of a large context window. The price is five plugins to version and test, a
multi-plugin marketplace repeated across every client manifest, and users who must find the packs.
Revisit if the always-on cost grows well past today's, or users ask for a smaller install.

## Descriptions keep a short summary, not only "Use when ..."

One plugin recommends descriptions that state only when to use a skill, so an agent cannot follow
a summary instead of reading the skill. Ours do summarise, and in the eval runs the right skill
loaded 40 times in 41 (see `evals/README.md`), so rewriting them would add risk for no observed
gain. Re-run `make evals` before and after any description change.

## No Codex agents

Agent files generated for Codex were valid, but a real Codex session exposed no selectable agent
type, so they could not be spawned (see `CLIENTS.md`). Revisit when Codex fixes this.

## No wholesale spec-driven workflow

Spec Kit, OpenSpec and BMAD cover ground our feature workflow already covers, at more weight.
We take ideas only, never wording.
