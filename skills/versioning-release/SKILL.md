---
name: versioning-release
description: Semantic versioning, Keep a Changelog, tags, release notes, deprecation before removal. Use when picking a version, updating the changelog, cutting a release, tagging, or planning a breaking change.
verified: 2026-11-07
---

# Versioning and releases

## Version numbers (MAJOR.MINOR.PATCH)

- **MAJOR**: a change that breaks existing users (removed or renamed behaviour,
  changed meaning). Mark it with `BREAKING CHANGE` in the commit.
- **MINOR**: new behaviour that stays compatible.
- **PATCH**: a fix that stays compatible.
- Before the first stable major release, the project may still change its public behaviour between minor
  versions. Say so in the changelog. Make the first stable major release when users depend on it.

The commit types map to these levels: `feat` is MINOR, `fix` is PATCH, and a
breaking marker is MAJOR. Check the list of commits since the last tag before
choosing the level, rather than guessing.

## Changelog (Keep a Changelog)

- `CHANGELOG.md` has an `## [Unreleased]` section at the top. Every user-visible
  change goes there as it lands, not at release time.
- Group entries under Added, Changed, Deprecated, Removed, Fixed, Security.
- Write for users: what changed for them and what they must do, not the file names.
- Each release gets a heading with its version and date: `## [X.Y.Z] - YYYY-MM-DD`.

## Releasing

1. Confirm `main` is green and the Unreleased section has entries.
2. Bump the version with the project's release command (for the plugin:
   `make release LEVEL=minor`). It updates every manifest and dates the changelog.
3. Review the diff, commit it with `chore(release): vX.Y.Z`.
4. Create an annotated tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
5. Push the commit and the tag. The release pipeline checks the tag matches the
   manifests and changelog, then publishes the notes.

Never move or re-create a published tag. If a release is wrong, release a new
version that fixes it.

## Deprecation

Deprecate in one MINOR release, say how to migrate, and remove in a later MAJOR
release. Removing something without a deprecation step is a breaking change.
