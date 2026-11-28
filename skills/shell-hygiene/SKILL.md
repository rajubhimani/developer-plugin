---
name: shell-hygiene
description: "Leave no process behind: time limits and background tracking. Use when running builds, tests, dev servers or long commands."
metadata:
  verified: "2026-11-17"
---

# Shell hygiene

A process you start is yours to finish or stop before you report.

## Rules

1. **Run in the foreground and wait.** Give a long command (build, full lint,
   integration tests, a service you are about to call) a longer time limit
   instead of backgrounding it.
2. **Background only what you use in the same session.** A dev server you are
   about to call, or a long run while you edit other files. Never park a slow
   command there, and never fire and forget.
3. **Account for every process you started.** When you write your report, each
   one has finished or been stopped by you.
4. **Wait, stop, or say so.** If one is still running, wait when you need its
   result, stop it when you do not, and name it in the report when you can do
   neither.

## Avoid

- Backgrounding the test suite only because it might take a minute.
- Starting a dev server and leaving it running when the work ends.
- Starting several background commands "in case". Run a command when you need it.
- Running probes, exploit attempts or destructive experiments in the shared
  working tree. Use a copy outside it, and never restore or check out files in
  the shared tree to undo a probe.
