---
name: refactoring
description: Change structure without changing behaviour: characterization tests, small reversible steps, seams, strangler replacements, debt. Use when cleaning up code, paying down debt, replacing a module, or when a change is hard because code is tangled.
verified: 2026-11-19
---

# Refactoring and technical debt

Refactoring changes structure and keeps behaviour. If behaviour changes, it is a
feature or a fix, and it gets its own change.

## Rules

1. **Have a safety net first.** If the code has no tests, write *characterization
   tests* that record what it does today (even if odd), then refactor under them.
   A refactor without tests is a guess.
2. **Small steps, tests green after each.** One move, run the tests, continue. If
   a step breaks things and the cause is not clear, revert it, do not push on.
3. **Never mix structure and behaviour** in one commit. Refactor commits change no
   test expectations; behaviour commits do. Reviewers can then trust the first
   kind at a glance.
4. **Keep the change reviewable.** A refactor that touches many files is a series
   of small pull requests, each safe to merge alone. No "while I was here"
   additions.
5. **Refactor in service of a goal:** the feature you are about to add, the bug
   you are about to fix. Make the change easy, then make the easy change. Avoid
   cleaning for its own sake in code nobody touches.
6. **Use tool-driven moves** (rename, extract, move) over hand edits where the
   editor or language server offers them; they are mechanical and safe.
7. **When code cannot be tested,** find a *seam* (a place to substitute behaviour
   without editing the code there): pass the dependency in, wrap the call, extract
   the pure part. Make only tiny mechanical changes until a test fits.
8. **Replace big things by strangling,** not rewriting. Put a thin layer in front,
   build the new path beside the old, move callers over a few at a time, keep a
   fast switch back, and delete the old path only when nothing uses it. If you
   cannot switch back quickly, you are doing a risky rewrite.
9. **Delete dead code.** Version control remembers it.

## Smells that point to a move

| Smell | Usual move |
|---|---|
| Long function, many nesting levels | Extract function, guard clauses |
| Same code in several places | Extract and name it (after the third) |
| Many parameters that travel together | Introduce a type for them |
| A type switch repeated | Polymorphism or a tagged union (see `design-patterns`) |
| One class changes for many reasons | Split by reason to change |
| Feature envy, a method using another object's data | Move it to that object |
| Primitive values with rules (ids, money) | Small value type |
| Deprecated API, option or dependency in use | Replace with the documented replacement, own commit, tests green |
| Comments explaining confusing code | Rename or extract so the code says it |

Smells are signals to look closer, not rules. A complexity number is a prompt to
review; each team sets its own limit and enforces it with the linter, not by
argument.

## Technical debt

- **Record it with an owner and a condition,** as a task or a marked comment
  (see `code-comments`), not as a vague wish.
- **Rank by pain and cost:** how often the code is touched, how often it breaks,
  and how cheap the fix is. High-churn, low-effort first.
- **Pay as you go:** budget a little in each change rather than a "cleanup
  quarter" that never lands.
- **Say no on purpose** to debt that does not hurt; record the decision so it is
  not proposed again (see `standing-decisions`).

## Related

`testing-strategy` (honest tests), `git-workflow`, `change-triage`.
