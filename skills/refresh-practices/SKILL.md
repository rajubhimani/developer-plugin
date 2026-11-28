---
name: refresh-practices
description: "Keep this plugin's guidance current. Use when asked to update its practices, or a skill's verified date is old."
metadata:
  verified: "2026-11-07"
---

# Refreshing practices

The guidance is split into two layers so it can last for years.

## Roots (change rarely, with a recorded reason)

Principles that stay true across tools and eras: least privilege, reproducible
builds, pinned inputs, small units with one job, explicit configuration, tests as
a gate, honest labels, docs that point to detail, and supply-chain integrity.
A root changes only when the principle itself was wrong, and the change is
recorded in `CHANGELOG.md` with the reason.

## Leaves (change often, always looked up)

Tool names, commands, flags, configuration syntax, version numbers, and vendor
recommendations. Never copy these from memory or from an old skill. Look them up
from the source named in the skill's "Current tools" or "Current versions"
section, at the time you need them.

## Review steps

1. Run `make versions` to see the current stable releases.
2. For each skill whose `metadata.verified` date is old, read the official docs it names
   and check that the commands and syntax still work.
3. Replace anything that no longer holds. If a new practice has replaced an old
   one, add it and remove the old one; do not leave both.
4. Set `metadata.verified` to today's date only after step 2 for that skill.
5. Add one line to `CHANGELOG.md`: the date, the skills changed, and why.
6. Run `make validate`. It fails on hard-coded version numbers and on stale dates.

## Adding a new topic

Write a skill with a short description that says when to use it, principles
first, then a "Current tools" section that says where to look things up. Keep the
main file under about 150 lines; move long material into a reference file that
the main file links to.
