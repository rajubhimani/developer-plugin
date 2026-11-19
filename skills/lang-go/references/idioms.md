# Go idioms and how to handle common concerns

Go's strengths: one static binary, a strong standard library, cheap concurrency and
a small language. Its costs: verbose error handling, easy goroutine leaks, nil
surprises. Lean on the strengths.

## Errors

- Errors are values: return them, check them, and add context where you handle
  them. `fmt.Errorf("loading invoice %d: %w", id, err)` keeps the cause; `%v` would
  break the chain.
- Inspect with `errors.Is` (a known value) and `errors.As` (a type), never by
  comparing text. Define sentinel errors or typed errors only for what callers
  branch on.
- **Handle an error once:** log it or return it, not both.
- Wrapping exposes the inner error to callers; do not wrap what you do not want to
  promise.
- Never ignore an error with `_` without a comment saying why. The linter should
  flag unchecked errors.
- `panic` is for programmer errors and impossible states, not for input. Recover
  only at a boundary (a server handler) to log and return a safe answer.
- Keep the happy path unindented: return early on error.

## Concurrency

- Every goroutine needs an owner and a way to stop. Pass a `context.Context` as the
  first argument, honour its cancellation at blocking points, and wait for the
  goroutines you start.
- Use `errgroup` to run related goroutines, stop the rest on the first error and
  collect it. Bound parallelism with its limit or a semaphore.
- Prefer sharing by passing values over channels or owning data in one goroutine;
  use a mutex for small shared state. Close a channel from the sender only.
- Give channels a clear direction in signatures. A goroutine that blocks on a send
  nobody receives is a leak; a buffer of one or a select on the context prevents it.
- Run tests with the race detector in CI. Treat any report as a bug.
- Do not start goroutines in `init` or at import time.

## Design

- Accept interfaces, return concrete types. Define an interface where it is used,
  small (one or two methods). Do not create an interface per struct.
- Make the zero value useful. Use functional options or a config struct for many
  options.
- Pass `context` and dependencies explicitly; avoid package-level mutable state.
- Keep packages by what they provide, short lowercase names, no `util` or `common`.
  Put internal code under `internal/`.
- Use generics when they remove real duplication over several types, not by
  default.

## Configuration and logging

- Read configuration once in `main`, into a typed struct, from the environment (and
  flags). Fail fast on a missing value. A local `.env` file loaded only in
  development is fine; the real environment wins (see `secrets-and-config`).
- Use the standard structured logger; JSON to standard output in production. Put
  request and trace ids in the context and log them (see `observability`).

## Testing

- Table-driven tests with named cases and `t.Run`; `t.Helper` in helpers;
  `t.TempDir` for files; `t.Setenv` for environment.
- Fake the dependencies you pass in; use a real database in a container for a few
  integration tests. Fuzz tests for parsers and decoders. Benchmarks before
  optimizing (see `performance`).
- Keep tests free of sleeps; wait on channels or conditions.

## HTTP services

- Set timeouts on the server and on every client; the defaults have none. Close
  response bodies. Limit request body size.
- Handle shutdown: on SIGTERM stop accepting, drain with a deadline, then exit
  (see `kubernetes`).
- Use the container's CPU limit awareness: check that the runtime sets its
  parallelism from the container limit, or set it explicitly, and tune memory
  limits to the container (look up the current runtime behaviour).

## Container recipe

- Build a static binary (cgo off unless you need it), strip debug info, trim paths,
  in a multi-stage build; run on a minimal base (distroless static, or scratch plus
  CA certificates and a time-zone database if needed) as a numeric non-root user.
- Cache order: copy `go.mod` and `go.sum`, download modules, then copy the source.
  Add BuildKit cache mounts for the module cache and the build cache so rebuilds
  reuse compiled packages.
- No shell in the final image means no shell-form `CMD` problems; the binary is
  process 1 and receives SIGTERM. Healthchecks are probes (see `kubernetes`), since
  the image has no tools to run one.
- Embed the version and commit at build time with linker flags, and expose them.

## Security

- Validate and bound all input; use parameterized queries; do not build shell
  commands from input; use `crypto/rand` for tokens.
- Run the vulnerability scanner for Go modules in CI (see `dependency-management`).
