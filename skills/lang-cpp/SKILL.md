---
name: lang-cpp
description: C++ project setup and quality gates (CMake presets, current C++ standard, clang-format, clang-tidy, sanitizers, vcpkg or Conan). Use when creating, changing, reviewing or building C++ code.
verified: 2026-11-07
---

# C++

## Current versions

Look these up when you start: CMake from `https://api.github.com/repos/Kitware/CMake/releases/latest`.
For clang-tidy and clang-format, use the current LLVM release at
`https://github.com/llvm/llvm-project/releases`. For the newest C++ standard
your compilers support, read the compiler release notes.

## Setup

- Use CMake with `CMakePresets.json`: at least `debug`, `release`, `asan` and
  `tsan`, so everyone builds the same way.
- Set the standard explicitly (`CMAKE_CXX_STANDARD` set to the current standard, required, no
  extensions).
- Put warning flags in one interface target that every target links to, rather
  than repeating them.
- Manage dependencies with vcpkg or Conan and commit the manifest. Pin versions.

## Quality gates

1. `clang-format --dry-run --Werror` on the sources.
2. Build with warnings as errors.
3. `clang-tidy` through the compile database. Include the bug-prone, performance,
   and modernize check families the team agrees on.
4. Tests (for example GoogleTest or Catch2) on every pull request.
5. Sanitizer presets (`asan`, `ubsan`, `tsan`) in CI.

## Common mistakes

- Raw `new` and `delete` where a value, `std::unique_ptr` or a container fits.
- Returning references or views to temporaries.
- Undefined behaviour from signed overflow, out-of-range indexing or use after
  move. Sanitizers catch many of these; run them.
- Header-only code that compiles slowly because it pulls in everything.

Source to check before relying on details: the C++ Core Guidelines, CMake
documentation, and the clang-tidy check list.
