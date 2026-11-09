# Coding standards

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

## Tests and checks

12. Deterministic logic gets tests. A bug fix adds a test that would have
    caught it.
13. Run the project's single check command (lint, format, types, tests)
    before reporting work done. Warnings count as failures. Say so plainly if
    a check could not run.

## Honesty

14. Mark data nobody has checked as DRAFT. State what a result does not show.
15. Never claim a test passed, or a step worked, without running it.

## Documentation

16. Every module has a short doc page: what it does, its public API, and how
    to use it. Keep the doc next to the code or in `docs/`.
17. Every folder that holds code or docs has an index (`README.md`) listing
    its contents with one line each and a link. Update the index in the same
    change that adds or removes a file.
18. Wrap Markdown at 80 columns.

## Git

19. Commit or push only when the user asks.
20. Commit messages, pull requests, code and docs carry no AI or tool
    attribution. The user is the only author.
21. Never rewrite pushed history without the user's explicit approval for
    that push.
