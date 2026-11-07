---
name: task-tracking
description: How to create, move, list and read feature tasks in a project using the make task targets, including the UTC log and the by field. Use when asked what is in progress, completed, rejected or in backlog, or to create or change a task's status.
verified: 2026-11-07
---

# Task tracking

Tasks are files in `docs/tasks/<status>/`. The folder is the status, and the
front matter says the same thing. Use the make targets so both always agree and
every change is logged.

## Commands

- `make tasks`: list each status with its tasks, and the start and completion
  times. Use this to answer "what is in progress?" instead of opening files.
- `make task-new FEATURE=<slug> TITLE="..." [REQ=REQ-NNN]`: create a task in backlog.
- `make task-move TASK=<id> STATUS=<status> [REASON="..."]`: change status.
  Statuses: `backlog`, `in-progress`, `completed`, `rejected`. Rejected needs a reason.

Never move task files by hand. A hand move skips the log and leaves the folder
and front matter out of step.

## The log

Each task ends with a log. Every line has a UTC timestamp (ending in `Z`), the
event, and `by`, the person who made the change. `by` is the GitHub login, then
the git name, then `unknown`. Do not edit old log lines; the log only grows.

## Git

Task moves use `git mv` when the project is a git repository, so history follows
the file. If git is missing, the tool prints how to install it. Ask the user to
install git rather than working around it. Projects should always be git repositories.

## Reading status

- Run `make tasks` once per session when status matters.
- Open a single task file only when you need its details.
- Do not summarise status from memory; re-read it.
