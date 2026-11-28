---
name: database-migrations
description: "Safe schema and data changes: expand and contract, backfills, rollback. Use when renaming, adding or dropping columns, tables or constraints."
metadata:
  verified: "2026-11-19"
---

# Database migrations

The schema and the running code change at different times. A deploy has old and
new code live together, and rollback must still work. Make every step safe for
both.

## Rules

1. **Migrations are versioned files in the repo,** reviewed like code, applied in
   order by a tool, never edited after they ship. Fix forward with a new one. Do
   not change the schema by hand in production.
2. **Each migration does one thing** and runs in a bounded time. Keep schema
   changes apart from large data changes.
3. **Expand, migrate, contract** for anything that is not purely additive:
   1. *Expand:* add the new column, table or index. Old code ignores it.
   2. *Migrate:* deploy code that writes both (or reads new, falls back to old),
      then backfill existing rows in small batches.
   3. *Contract:* after every reader uses the new shape and it is verified,
      stop writing the old one, deploy, and only then drop it in a later release.
4. **Safe on their own:** adding a nullable column, a new table, a new index built
   without blocking writes.
5. **Risky, so use expand and contract:** rename, drop, type change, adding a
   required column or constraint to existing data, splitting or merging tables.
   A rename is add, copy, switch, drop; never one step.
6. **Know your database's locks.** Which statement blocks reads or writes, and for
   how long, depends on the engine and its version: look it up in its docs, test
   on production-sized data, and set a lock timeout so a stuck migration fails
   instead of queuing everything behind it.
7. **Backfill in batches** with a pause and a resume point, off the peak hour,
   monitoring load and replication lag. A backfill is idempotent so it can be
   rerun.
8. **Separate rollback of code from rollback of schema.** Roll the application
   back first; the previous code must work with the expanded schema. A schema
   "down" step that destroys data is not a rollback plan: take a backup or keep
   the old column until the contract step.
9. **Order the release:** migrate (expand), deploy code, verify, then contract.
   Never deploy code that needs a column before it exists.
10. **Test it:** run the migration on a copy with realistic data, run it twice,
    run the old code against the new schema, and test the rollback path.
11. **Protect data:** no real personal data in migration files or fixtures, and
    note retention or deletion duties for new fields.

## In the task and PR

State the risk (data loss, long lock), the order of steps, the verification query
and the rollback line. The deploy reviewer checks all four (see `ci-cd`,
`git-workflow`).

## Current tools

Pick the migration tool the language skill names and look up its commands. Look
up the lock behaviour of the exact database and version in use.
