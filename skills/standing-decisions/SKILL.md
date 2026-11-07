---
name: standing-decisions
description: Record and respect decisions the user has already made, such as rejected tasks or chosen options, so they are not proposed again. Use when the user rejects an option or task, makes a choice, or when you are about to propose something that may already have been decided.
verified: 2026-11-07
---

# Standing decisions

The user should not have to repeat a decision. Decisions are stored in the
project so every session and every agent sees them.

## Before proposing something

Read the "Standing decisions" section of `AGENTS.md`. If your proposal matches a
rejected item or a decided item, do not propose it again. Mention the earlier
decision only if the user's situation has changed.

## Recording a decision

- The user rejects a task: `make task-move TASK=<id> STATUS=rejected REASON="..."`.
  Use the user's own words for the reason where you can.
- The user makes a decision outside a task: `make decide TEXT="..."`. Write one
  clear sentence: what was chosen and what was ruled out.
- Refresh the list with `make decisions-sync` if you edited the logs by hand.

## Changing a decision

If the user changes their mind, do not delete the old record. Reopen the task
with `make task-move TASK=<id> STATUS=backlog`, which removes it from the standing
list, or record the new decision with `make decide`, which keeps the history.

## Rules

- Record a decision once, when it is made.
- Keep decision text short and free of secrets, because it is committed to git.
- Ask before recording a decision the user did not clearly make.
