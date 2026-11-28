---
name: architecture-decisions
description: "Short decision records. Use when choosing a framework, pattern or data store, reversing a choice, or asked why something is built this way."
metadata:
  verified: "2026-11-19"
---

# Architecture decision records

A decision record keeps the *why* when the people who knew it have moved on. It is
short, dated and not edited after it is accepted.

## When to write one

- The choice is costly to reverse (data store, language, framework, boundary, API
  shape, security model).
- People disagreed, or you rejected an obvious option.
- A future reader would ask "why on earth did they do it this way?".

Do not write one for a routine choice. Rejected tasks and small preferences go in
`standing-decisions`.

## Where

`docs/decisions/NNNN-short-title.md` (or the project's chosen folder), numbered in
order, linked from the docs index. Propose it in the same pull request as the
change so reviewers read the reason beside the code.

## Template

```markdown
# NNNN. Title in plain words

Status: proposed | accepted | superseded by NNNN | deprecated
Date: YYYY-MM-DD
Deciders: names or roles

## Context
The problem and the forces: requirements, limits, what is known and unknown.

## Options considered
1. Option A: what it is, gains, costs.
2. Option B: ...
(Include "do nothing".)

## Decision
What we chose, in one or two sentences, and why it beats the others.

## Consequences
What gets easier, what gets harder, what we must now do, and what would make us
revisit this (a trigger, not a date).
```

## Rules

1. **Write it when you decide,** not after; the rejected options are forgotten
   fast.
2. **Keep it to one page,** one decision per record. Link evidence (a research
   note, a benchmark) instead of pasting it.
3. **Never rewrite an accepted record.** To change course, write a new record
   that supersedes it, and mark the old one superseded with a link.
4. **State the trade-off honestly,** including the downside you accepted.
5. **Name the revisit trigger,** such as a load level, a cost, or a team change.

## Organize docs by purpose

Keep four kinds apart so each reader finds what they need:

- **Tutorials:** learn by doing a guided first success.
- **How-to guides:** steps for a specific task.
- **Reference:** exact facts (commands, options, API); generated where possible.
- **Explanation:** background and reasoning; decision records live here.

## Related

`docs-and-index`, `standing-decisions`, `writing-style`, `architecture-monolith-vs-services`.
