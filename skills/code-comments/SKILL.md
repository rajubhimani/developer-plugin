---
name: code-comments
description: How to write and maintain code comments and docstrings: explain why, not what; keep them true; mark debt with an owner and a condition. Use when writing or reviewing code, or when a comment looks wrong or out of date.
verified: 2026-11-07
---

# Code comments

## Principles

- **Explain why, not what.** The code already shows what it does. A comment says
  why this approach was chosen, what a constraint is, or what trap it avoids.
- **Good names first.** If a comment is needed to explain what code does, rename
  the thing or split the function, then drop the comment.
- **Comment the gaps code cannot express:** external library quirks, business rules,
  performance trade-offs, the reason for an odd-looking workaround.
- **Stale comments are worse than none.** Update or delete a comment in the same
  change as the code it describes. Review comments in diffs.
- **Do not comment every line.** Redundant comments add reading cost for no gain.

## Debt markers

Use one marker per item, with an owner or the requirement it waits for, and a
condition for removal:

    # TODO(rajubhimani): drop this shim once REQ-007 ships

The owner and condition are team conventions chosen for this plugin, not a
language standard. Use the team's name format.

## Docstrings

- Public modules, classes and functions get a docstring in the language's usual
  style (see the matching `lang-*` skill). Say what the thing is for and when to use it.
- A docstring describes the contract: inputs, outputs, errors. It does not repeat
  the implementation.

## When reviewing

- Flag a comment that contradicts the code.
- Flag a workaround with no reason, and a TODO with no owner or condition.
