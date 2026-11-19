# C++ idioms and how to handle common concerns

C++'s strengths: zero-cost abstraction, deterministic cleanup and fine control. Its
costs: undefined behaviour, a large language and long builds. Use the modern subset
the Core Guidelines describe, and enforce it with tools.

## Ownership and resources

- **RAII for everything:** memory, files, locks, sockets. A resource is owned by an
  object whose destructor releases it. No naked `new` and `delete`; no owning raw
  pointers.
- Default to values and references. Use `unique_ptr` for single ownership,
  `shared_ptr` only for real shared ownership (and break cycles with `weak_ptr`).
  Raw pointers and references mean "borrowing" and must not outlive the owner.
- Rule of zero: let members manage themselves. If you write one of the special
  members, define or delete all of them.
- Prefer `span`, `string_view`, ranges and algorithms to pointer arithmetic and hand
  loops. Use `array` and `vector`; use `.at()` or checked access where bounds matter.
- `const` by default, `constexpr` where it fits, `enum class`, `override`, `explicit`
  constructors and `[[nodiscard]]` on results that must be used.
- Avoid dangling views: do not return a view of a temporary or store one past its
  owner's life.

## Errors

- Pick one strategy per codebase and layer: exceptions for exceptional failures, or
  a result/expected type for expected ones. Destructors never throw. Functions that
  cannot fail are `noexcept`.
- Throw by value, catch by const reference, derive from the standard exception
  hierarchy. Keep the cause when translating. RAII makes cleanup safe on every path.
- Check preconditions at public boundaries; use assertions for internal invariants.
- Do not ignore return values of status-returning functions.

## Design

- Prefer composition and small interfaces; use virtual functions where behaviour
  varies at run time, templates and concepts where it varies at compile time. Keep
  templates simple and error messages readable with constraints (see
  `design-patterns`).
- Headers expose the minimum; hide details in the source or a private namespace.
  Forward declare to cut build time. One-definition-rule care with inline and
  templates.
- Avoid global mutable state and static initialization order dependencies.
- Use the standard library first; add a dependency only for a clear need (see
  `dependency-management`).

## Concurrency

- Use the standard threads, `jthread`, mutexes with scoped lock types, atomics and
  futures; never lock and unlock by hand. Keep lock order fixed. Prefer message
  passing and immutable data; use the thread sanitizer in CI. Honour stop tokens for
  cooperative cancellation (see `concurrency`).
- Do not detach threads. Join or use an owner that joins.

## Testing and verification

- Unit tests with the project's framework, including error and boundary cases;
  deterministic (inject clocks and I/O).
- Build with strict warnings as errors; run under the address and undefined-behaviour
  sanitizers and, separately, the thread sanitizer in CI. Use the clang-tidy checks
  for the Core Guidelines and bug-prone patterns, with a blocking policy.
- **Fuzz parsers and decoders** of untrusted input. Benchmarks before optimizing
  (see `performance`).
- Consider hardened standard library modes that add bounds and null checks in debug
  and test builds.

## Configuration and logging

- Parse configuration once into a typed struct; environment wins over a local file;
  fail fast. Use a structured logging library; never log secrets (see
  `observability`, `secrets-and-config`).

## Container recipe

- Multi-stage with the toolchain in the build stage; use the dependency manager's
  cache (and BuildKit cache mounts) and a compiler cache so rebuilds are quick; copy
  only the binary and the shared libraries it needs to a minimal runtime base that
  has the matching standard library, or link statically for scratch or distroless.
- Numeric non-root user, exec-form entrypoint, SIGTERM handled through the main loop
  (flag set in the handler). Hardening compiler and linker flags on; debug symbols
  kept separately.

## Security

- All input hostile: validate sizes and ranges, no unchecked casts, no format-string
  misuse, no use after move. Use the secure random source and a vetted crypto
  library. Keep dependencies patched and scanned.
