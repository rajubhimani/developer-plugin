---
name: git-workflow
description: Git practice for branches, commits, messages, pull requests, merges and history safety, and what must never be committed. Use when creating a branch, committing, writing a commit message, opening or reviewing a pull request, merging, or before any history-changing command.
verified: 2026-11-07
---

# Git workflow

Every project set up with this plugin is a git repository. The user is the only
author of commits, pull requests and docs: never add tool or AI attribution
(no "Co-Authored-By", no "Generated with" lines).

## Branches

- Work on `main` only through pull requests. Protect `main`: require a review
  and passing checks.
- Keep branches short-lived, ideally under a day or two. Merge small, finished
  steps often; hide unfinished work behind a switch rather than a long branch.
- Name branches for the task: `checkout-04-apply-discount`.

## Commits

- One logical change per commit. A commit should build and pass the checks.
- Subject: `type(scope): imperative summary`, about 50 characters, no full stop.
  Types follow Conventional Commits: `feat` (new behaviour), `fix` (a bug),
  `docs`, `refactor`, `test`, `chore`, `ci`, `build`.
- Body (when the reason is not obvious): wrap at 72 columns and explain why,
  not what. Link the requirement or task ID, for example `Refs: REQ-003, checkout-04`.
- Breaking change: add `!` after the type or a footer `BREAKING CHANGE: ...`.
- A commit template lives in `.gitmessage`. Enable it once with
  `git config commit.template .gitmessage`.

## Pull requests

- Keep them small enough to review in one sitting. Describe what changed, why,
  which requirement it covers, and how it was tested.
- The pull request template in `.github/pull_request_template.md` lists the checks.
- Squash-merge a branch with messy work-in-progress commits. Keep a merge commit
  only when the individual commits matter.
- Reviews are for the code, not the author. Ask questions before requesting changes.

## History safety

- Never force-push a protected branch, and never rewrite a commit others have pulled.
- To update your own pull request branch after a rebase, use
  `git push --force-with-lease`, never a plain `--force`.
- Ask the user before any command that rewrites history, deletes branches, or
  discards uncommitted work (`reset --hard`, `clean -fd`, `checkout --`).
- Tags and releases: see the `versioning-release` skill.

## Never commit

- Secrets: `.env` files, keys, tokens, credentials. If one was committed, rotate
  the secret first, then remove it from history with the user's approval.
- Build output, caches, dependency folders, editor and OS files. The `.gitignore`
  covers them; extend it rather than force-adding files.
- Generated files that a build recreates.

## Line endings

`.gitattributes` sets text files to LF, so Windows and macOS clones do not show
every line as changed.
