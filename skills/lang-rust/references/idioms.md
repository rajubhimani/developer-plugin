# Rust idioms and how to handle common concerns

Rust's strengths: memory safety without a collector, data-race freedom in safe code,
expressive types and fast, small binaries. Its costs: a learning curve, long
compile times and async complexity. Let the compiler carry the proofs.

## Errors

- Return `Result`; use `?` to propagate. Do not `unwrap` or `expect` in library or
  request-handling code; reserve them for tests and for states that are truly
  impossible, with a comment saying why.
- **Libraries** define typed errors (an enum per failure kind, with a derive helper
  for display and conversion) so callers can match. **Applications** may use one
  catch-all error type with context for the top level. Do not return the catch-all
  from a library.
- Add context at each layer (what you were doing); keep the source error attached.
- `panic` is for bugs. Set the release profile so a panic aborts or is caught at the
  boundary deliberately.
- Make invalid states unrepresentable: enums for states, newtypes for ids,
  builders for many options, the type-state pattern for protocols.

## Ownership and design

- Borrow by default, clone on purpose. If you clone to quiet the borrow checker,
  rethink the data flow.
- Prefer iterators and combinators to index loops. Take `&str` and slices as
  parameters, return owned types when the caller needs ownership.
- Keep `unsafe` out, or confine it to one small module with a safety comment on
  each block, a safe wrapper and tests (run under the interpreter that detects
  undefined behaviour). Forbid it elsewhere with a lint.
- Traits for behaviour you want to swap; generics when the type is known at compile
  time, trait objects when it varies at run time. Do not over-generalize.
- Derive the common traits; implement them by hand only when behaviour differs.

## Concurrency and async

- The compiler's `Send` and `Sync` rules stop data races in safe code; design with
  ownership transfer (channels) before shared locks.
- Use an async runtime only for I/O-bound services. Never block inside async code;
  use the runtime's blocking pool for blocking or CPU work.
- Know that a future can be dropped at any `await`: keep each step safe to cancel,
  or finish critical sections without yielding. Put a timeout on every external
  call and use cancellation tokens for shutdown (see `resilience`).
- Do not hold a standard lock across an `await`. Bound channels and task counts.
- Use scoped tasks or a join set so no task outlives its owner.

## Configuration and logging

- Parse configuration once into a typed struct (environment, then optional local
  file); the environment wins; fail fast with the setting's name. Wrap secrets in a
  type that does not print (see `secrets-and-config`).
- Use a structured, span-based logging and tracing crate; JSON to standard output
  in production; correlate with trace ids (see `observability`).

## Testing

- Unit tests beside the code, integration tests in the tests folder, doc tests as
  living examples. Property tests for parsers and invariants; fuzz targets for
  untrusted input; snapshot tests with care.
- Run clippy with warnings as errors, rustfmt, and the dependency policy and audit
  tools in CI.
- Use feature flags sparingly and test the combinations that ship.

## Container recipe

- Multi-stage build. To cache dependencies, use a dependency-planning tool (the
  common one builds a recipe, then compiles only dependencies in a cached layer) or
  BuildKit cache mounts for the registry and target directories.
- Release profile for production: optimized, with link-time optimization and a
  single codegen unit if build time allows, symbols stripped.
- Runtime base: distroless or a slim image for the default C library; a fully static
  build (musl target) can run on scratch, but check the allocator and TLS library
  trade-offs. Prefer a pure-Rust TLS stack to avoid linking system libraries.
- Numeric non-root user, exec-form entrypoint, handle SIGTERM through the runtime's
  signal support, probes from the cluster (see `kubernetes`).
- Copy only the binary and needed assets (CA certificates, migrations).

## Security

- Audit and deny known-vulnerable or unmaintained crates and unwanted licenses in
  CI (see `dependency-management`). Review new dependencies, build scripts and
  procedural macros; they run code at build time.
- Constant-time comparison for secrets; a vetted crypto library; no custom crypto.
