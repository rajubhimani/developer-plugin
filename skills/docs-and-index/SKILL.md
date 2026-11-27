---
name: docs-and-index
description: "Documentation for code: a page per module and an index README per folder. Use when adding, moving or removing code or docs, or when asked to document a project."
verified: 2026-11-07
---

# Docs and index

Apply the `coding-standards` rules as well. This skill covers the docs layout.

## Steps

1. Find the folders that hold code or docs. Skip build output, caches and
   dependency folders.
2. For each module, make sure a doc page exists. A doc page states:
   - what the module does, in one or two sentences;
   - its public functions, classes or commands, each with a one-line summary;
   - one short usage example if the API is not obvious;
   - links to the modules it depends on and to its tests.
3. For each folder, make sure a `README.md` index exists. It lists every
   file and subfolder with a one-line description and a relative link, in
   alphabetical order.
4. Add a root `docs/INDEX.md` (or the project's equivalent) that links to every
   folder index. Keep it as the entry point for navigation.
5. When a file is added, renamed or removed, update the index of its folder
   and the root index in the same change. Remove links to deleted files.
6. Keep every page at or under 80 columns per line.

## Checks before reporting done

- Every link resolves to an existing file.
- Every public name in a module appears in its doc page.
- No index lists a file that no longer exists.

Say which checks you ran. If a check was skipped, say so.
