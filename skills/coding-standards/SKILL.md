---
name: coding-standards
description: "Coding standards for every change: latest stable versions, structure, style, tests, docs and index pages, and git rules. Use whenever writing, changing or reviewing code or docs."
verified: 2026-11-07
---

These rules apply to every task that writes or changes code.

## Versions

1. Before adding or upgrading any library, framework or tool, look up its
   current stable version and its official docs. Do not rely on memory for
   versions or APIs.
2. Use the latest stable release. Pin exact versions in the lock file. In
   manifests, allow compatible updates only: patch and minor, never a new
   major (caret ranges such as `^X.Y.Z` in npm, or `>=X.Y,<X+1` in Python).
   Upgrade deliberately (for example `uv lock --upgrade`, `npm outdated`) and
   re-run the checks after each upgrade.
3. Do not use pre-release, beta or deprecated APIs unless the user asks.

## Structure

4. One job per module. Shared helpers live in one module and are never
   copied into a second file.
5. Depend on interfaces, not concrete classes. Use Protocols or abstract
   types so an implementation can be swapped. Use a registry or factory
   instead of long if/else chains when adding variants.
6. Configuration is explicit. Every setting is a typed, checked field of one
   settings object. Read the environment in one place only. No magic numbers
   inside functions.
7. Use an existing, well-tested library function instead of writing your own
   (for example `np.mean`, a tensor padding helper, a date parser). Search the
   libraries the project already depends on first. Write your own only with a
   reason you can state in a comment, such as a bug, a licence, or a
   deprecated call the library still makes. Guard against empty input before
   calling a function that reduces a collection (mean, max).

## Style

8. Give every public function, class and module type hints and a docstring.
   Docstrings say why, not what the code already shows.
9. Prefer dataclasses, Protocols and enums over loose dicts and tuples.
   Define a fixed set of values once, as an enum; never as a type of string
   literals plus a second list of the same values. Keep functions small.
10. Do not use `eval`, `exec`, bare `except:`, silent `except`, or mutable
   default arguments.
11. Comments explain a decision or a trap, not the next line.
12. Call by name. Pass arguments to your own functions and classes by keyword
    (`Token(id=1, form=word)`), one per line when the call does not fit on one
    line. The exceptions are a call with a single obvious argument (`len(xs)`),
    a library function that only accepts positional arguments, a callback
    typed `Callable[[A, B], R]`, which has no parameter names, and the
    `*args` part of a variadic call. Mark
    parameters that callers must name keyword-only with `*` in the definition.

## Tests and checks

13. Deterministic logic gets tests. A bug fix adds a test that would have
    caught it.
14. Run the project's single check command (lint, format, types, tests)
    before reporting work done. Warnings count as failures. Say so plainly if
    a check could not run.

## Honesty

15. Mark data nobody has checked as DRAFT. State what a result does not show.
16. Never claim a test passed, or a step worked, without running it.

## Documentation

17. Every module has a short doc page: what it does, its public API, and how
    to use it. Keep the doc next to the code or in `docs/`.
18. Every folder that holds code or docs has an index (`README.md`) listing
    its contents with one line each and a link. Update the index in the same
    change that adds or removes a file.
19. Wrap Markdown at 80 columns.

## Maintained code

23. Choose maintained libraries. Before adding a dependency, check that it is
    maintained: a release or commit within the last year or so, issues and
    security reports answered, not archived or marked deprecated, and a licence
    you can use. Prefer the standard library, then a library the project
    already uses, then a well-known maintained one. When a dependency you use
    stops being maintained, replace it with a maintained one as its own change.
24. Update deprecated code when you find it. A deprecated API, call, option,
    configuration key, dependency or practice found in code you read or change
    is replaced with its documented replacement now, as its own small change (a
    separate commit) with the tests green; do not leave it for later. The
    project's checks treat deprecation warnings as errors so none is missed. If
    the replacement changes behaviour users can see, or the migration is too
    large for one change, say so, record a task with an owner, and follow
    `versioning-release`; do not leave it silently.
25. Say what you replaced: list each deprecation and its replacement in the
    commit message or the report.

## Git

20. Commit or push only when the user asks.
21. Commit messages, pull requests, code and docs carry no AI or tool
    attribution. The user is the only author.
22. Never rewrite pushed history without the user's explicit approval for
    that push.
