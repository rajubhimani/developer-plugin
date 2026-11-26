---
name: handoff
description: Write a handoff note so a fresh session can continue this work. Use only when the person types /handoff or asks to end this session and carry on in a new one.
disable-model-invocation: true
verified: 2026-11-27
---

# Handoff

A long session carries stale context, and every turn pays for it. A fresh session with a short
note is cheaper and sharper. Write that note; do not start the new work yourself.

## Write the note

Save it to the system temp folder (`$TMPDIR`, else `/tmp`; `%TEMP%` on Windows) as
`handoff-<topic>.md`, or to a path the person names. Do not commit it.

Include, briefly:

1. **Goal:** what the work is for, in one or two sentences.
2. **State:** what is done, what is half done, what is not started.
3. **Decisions and why:** choices the person made or you made, and the reason, so they are
   not reopened (see `standing-decisions`).
4. **Where things are:** files touched, branch, commits, open pull request, by path or link.
5. **How to check:** the commands to run and what they should show now.
6. **Open questions** and the single **next step**.
7. **Skills to load** for the next session, by name.

## Rules

- Point, do not paste. If it is in a spec, plan, issue, commit or diff, give its path or link.
- Separate what you verified from what you only believe. Quote results you ran.
- Redact keys, passwords and personal data. Never copy a secret into the note.
- Keep it to what the next session needs; a long note defeats the purpose.

## Finish

Tell the person the path, and give one line to start the new session, for example
`Read /tmp/handoff-auth.md and continue with the next step.`
