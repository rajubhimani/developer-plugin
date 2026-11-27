---
name: feature-workflow
description: "The path for building a feature in a project set up with this plugin: requirement, feature file, tasks, tests, completion. Use when asked to start, plan, build or finish a feature."
verified: 2026-11-07
---

# Feature workflow

Every feature follows the same path, so anyone can see where it stands.

1. **Requirement.** Check `docs/requirements.md`. If the change needs a new
   requirement, add one line with the next free ID (REQ-NNN). Never reuse an ID.
2. **Feature.** `make task-new FEATURE=<slug> TITLE="..." REQ=REQ-NNN` creates the
   feature file on first use. A new feature must name the requirement it serves.
3. **Tasks.** Break the feature into small tasks. Each new task starts in backlog.
   Check the standing decisions (see the `standing-decisions` skill) before you
   propose a task that may already have been rejected.
4. **Build.** Move a task with `make task-move TASK=<id> STATUS=in-progress`
   before you start it. Keep only the tasks you are actively working on in progress.
5. **Test.** Write a test whose comment names the requirement, for example
   `# REQ-003`, and where it fits, the task ID. A feature is not done without it.
6. **Finish.** Run `make check`. Then `make task-move TASK=<id> STATUS=completed`.
   Do not mark a task completed if its tests fail or were skipped.
7. **Report.** Say what changed, which requirement it covers, and what you did
   not verify. Show the task list with `make tasks` when asked for status.

## Agents

When the plugin's agents are available, use them for the steps above and follow
the `agent-handoff` skill: requirements, design, test plan, plan, red tests,
build and review are done by separate agents, and the person approves
requirements, design, plan and merge.

## Rules

- Work from the task files, not from memory of what was discussed.
- If the user rejects an option, record it with the `standing-decisions` skill
  instead of asking again later.
- Keep each change small enough to review in one sitting.
