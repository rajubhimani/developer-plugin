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

One plugin recommends descriptions that state only when to use a skill. Ours keep a few topic words
and then the trigger, in the words people use, and the eval suite passes with them (see
`evals/README.md`). Re-run `make evals` before and after any description change.

## No `paths` field to hide language skills

A probe skill limited to Go files stayed in the skill list, with its description, in an empty folder.
It saves nothing on the list, so shorter descriptions are how we save space.

## Agents keep `model: inherit` and no `effort`

A pinned model would override the choice of someone who runs a cheaper or stronger one, and we have
no measurement showing a lower effort keeps agent quality. Each agent does have `maxTurns`, a
generous cap against runaway runs; a capped agent returns its work marked partial.

## No Codex agents

Agent files generated for Codex were valid, but a real Codex session exposed no selectable agent
type, so they could not be spawned (see `CLIENTS.md`). Revisit when Codex fixes this.

## No wholesale spec-driven workflow

Spec Kit, OpenSpec and BMAD cover ground our feature workflow already covers, at more weight.
We take ideas only, never wording.
