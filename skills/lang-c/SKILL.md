---
name: lang-c
description: C project setup and quality gates (current C standard, strict warnings, sanitizers, clang-tidy, CMake). Use when creating, changing, reviewing or building C code.
verified: 2026-11-07
---

# C

## Current versions

Look these up when you start: CMake from `https://api.github.com/repos/Kitware/CMake/releases/latest`.
For clang-tidy and clang-format, use the current LLVM release listed at
`https://github.com/llvm/llvm-project/releases`. For the newest C standard your
compilers support, read the GCC and Clang release notes.

## Setup

- Build with CMake. Set the standard explicitly, set to the current standard
  with `C_STANDARD_REQUIRED ON`. Use an older standard only if older compilers must build it.
- Export `compile_commands.json` (`CMAKE_EXPORT_COMPILE_COMMANDS ON`) so
  clang-tidy and editors read the same build.
- Keep headers small and include what you use. Every header has an include
  guard or `#pragma once`.

## Quality gates

1. Build with warnings as errors: `-Wall -Wextra -Wpedantic -Werror` on GCC and
   Clang, `/W4 /WX` on MSVC.
2. Debug builds with `-fsanitize=address,undefined`. Run ThreadSanitizer in a
   separate build, because it cannot be combined with AddressSanitizer.
3. `clang-tidy` on the compile database. Enable the bug-prone and security
   checks the team agrees on.
4. Tests in CI on every pull request. Run the sanitizer build in CI too.

## Common mistakes

- Buffer sizes computed without checking the input length.
- Integer overflow in size calculations before an allocation.
- Ignoring the return value of functions that report errors.
- Unchecked `malloc` results.

Source to check before relying on details: the C standard working drafts, the
GCC and Clang manuals, and the clang-tidy check list.

## Deeper guide

`references/idioms.md` covers how this language handles errors, concurrency,
configuration, logging, testing, security and the container image, and where it
differs from the others. Read it when you design or review more than a small edit.
