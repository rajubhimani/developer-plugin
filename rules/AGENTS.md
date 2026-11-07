# Developer plugin rules

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

## Style

7. Give every public function, class and module type hints and a docstring.
   Docstrings say why, not what the code already shows.
8. Prefer dataclasses, Protocols and enums over loose dicts and tuples.
   Keep functions small.
9. Do not use `eval`, `exec`, bare `except:`, silent `except`, or mutable
   default arguments.
10. Comments explain a decision or a trap, not the next line.

## Tests and checks

11. Deterministic logic gets tests. A bug fix adds a test that would have
    caught it.
12. Run the project's single check command (lint, format, types, tests)
    before reporting work done. Warnings count as failures. Say so plainly if
    a check could not run.

## Honesty

13. Mark data nobody has checked as DRAFT. State what a result does not show.
14. Never claim a test passed, or a step worked, without running it.

## Documentation

15. Every module has a short doc page: what it does, its public API, and how
    to use it. Keep the doc next to the code or in `docs/`.
16. Every folder that holds code or docs has an index (`README.md`) listing
    its contents with one line each and a link. Update the index in the same
    change that adds or removes a file.
17. Wrap Markdown at 80 columns.

## Git

18. Commit or push only when the user asks.
19. Commit messages, pull requests, code and docs carry no AI or tool
    attribution. The user is the only author.
20. Never rewrite pushed history without the user's explicit approval for
    that push.
