# C idioms and how to handle common concerns

C's strengths: tiny, fast, portable code with direct control. Its costs: no bounds
checking, manual memory, undefined behaviour and no built-in error type. Safety
comes from discipline plus tools, so make both mandatory.

## Memory and ownership

- Every allocation has one owner and one place that frees it. Document ownership in
  the function comment: who frees, who borrows.
- Pair allocate and free in the same module. Set a pointer to null after freeing.
  Check every allocation result.
- Pass a pointer and a length together (or a small struct holding both); never rely
  on a terminator you did not check. Use the bounded string and memory functions and
  check their results; do not use the unbounded ones.
- Use sized, fixed-width integer types for data formats; beware signed overflow,
  conversions and shifts, which are undefined or lossy.
- Initialize every variable. Prefer stack and static buffers of known size to the
  heap when the size is bounded.
- Use the cleanup-attribute or `goto cleanup` pattern for one exit path that frees
  everything in reverse order.

## Errors

- Return a status (an enum or a negative code) and pass results through output
  parameters. Check every return value; mark functions so the compiler warns when a
  result is ignored.
- Do not hide errors in global state; if you use `errno`, read it at once.
- Fail early on invalid arguments at the public boundary; use assertions for
  internal invariants (and keep them in test builds).
- Clean up on every error path (see above).

## Design

- Small functions, one job. Opaque types (a struct declared in the header, defined in
  the source) hide the layout. A header exposes the minimum; include guards; no
  definitions in headers.
- Mark everything file-private `static`. Use `const` wherever data is read-only.
- Keep the build warnings strict, and treat them as errors (see the main skill).
- Avoid macros that act like functions; prefer inline functions and constants.

## Concurrency

- Threads share memory: protect shared data with the standard mutexes or atomics;
  keep lock order fixed; never share stack data with a thread that may outlive it.
  Run the thread sanitizer in CI (see `concurrency`).
- Signal handlers may only do async-signal-safe work: set a flag and return.

## Testing and verification

- Unit tests for each function, including error and boundary cases (zero, maximum,
  null, empty). Run the whole suite under the address and undefined-behaviour
  sanitizers in CI; run the memory checker on release candidates.
- **Fuzz every parser and decoder** that reads untrusted bytes, and keep the corpus.
  Static analysis in CI with a blocking policy.
- Deterministic tests: no real time or network; inject them.

## Configuration and logging

- Read configuration once at start-up into a struct; validate; fail fast. Logs go to
  standard error or output in a structured line format with a level; never log
  secrets (see `observability`, `secrets-and-config`).

## Container recipe

- Multi-stage: build with the compiler toolchain, run on a minimal base (a static
  build can use scratch or distroless; a dynamic one needs the matching C library).
  Copy only the binary. Numeric non-root user, exec-form entrypoint, handle SIGTERM
  by setting a flag in the handler and shutting down in the main loop.
- Build with hardening flags (stack protector, fortify, position-independent
  executable, full relro) and keep debug symbols in a separate file.
- Cache the dependency build layer before copying the source.

## Security

- Treat all input as hostile; check sizes before copying; avoid format-string
  misuse (always a constant format); use the secure random source; zero secrets
  after use with a function the compiler cannot remove.
