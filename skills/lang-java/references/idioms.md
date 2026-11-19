# Java idioms and how to handle common concerns

Java's strengths: a mature ecosystem, strong tooling, a fast and observable runtime
and long-term compatibility. Its costs: verbosity, framework magic and a heavy
start-up and memory footprint in containers. Use the modern language features and
keep framework magic visible.

## Language

- Use records for immutable data, sealed types with pattern matching for closed sets
  of cases, `Optional` for a return that may be empty (not for fields or
  parameters), and the collection and stream libraries for transformation.
- Make classes and fields final by default; prefer immutability; minimize mutable
  shared state.
- Null: do not return null for collections; validate at the boundary with
  `Objects.requireNonNull`; use the nullness annotations your tooling checks.
- Prefer composition and small interfaces (see `design-patterns`). Keep framework
  annotations out of the domain model where the domain is complex (see
  `domain-modeling`).

## Errors

- Use unchecked exceptions for programming errors and unrecoverable states; checked
  exceptions only where the caller can reasonably recover. Do not catch `Exception`
  or `Throwable` except at a boundary. Never an empty catch.
- Always keep the cause: `new DomainException("loading invoice 42", cause)`.
- Close resources with try-with-resources. Do not use exceptions for flow control.
- Translate exceptions at layer boundaries into one error model; web handlers return
  problem-details responses with no stack trace (see `error-handling`, `api-design`).

## Concurrency

- Prefer the high-level executors, structured concurrency where available, and
  immutable messages over raw threads and shared state. Know that blocking threads
  are costly; the lightweight virtual threads suit blocking I/O work, but check
  that libraries do not pin them, and do not pool them.
- Use concurrent collections and atomics; synchronize on private locks; avoid
  holding locks while calling out. Always set timeouts on external calls and respect
  interruption (restore the flag, stop work).
- Use the thread sanitizer-equivalent checks your tooling offers and stress tests
  (see `concurrency`).

## Spring-style services

- Constructor injection only; no field injection. Keep controllers thin, services
  transactional where needed, repositories simple.
- **Transactions:** keep them short; do not call remote services inside one; know
  where the proxy boundary is (a self-call skips it). Watch for N+1 queries from
  lazy loading (see `performance`).
- Validate input with the bean validation annotations at the controller; DTOs are
  separate from entities.
- Configuration through typed, validated properties classes, one per concern,
  bound from the environment; profiles select values, not behaviour (see
  `secrets-and-config`).
- Database changes through a migration tool, never schema auto-update in
  production (see `database-migrations`).

## Logging and observability

- A logging facade with structured JSON output in production; put the trace id in
  the logging context; never log secrets or personal data; use the metrics and
  tracing integrations the framework provides (see `observability`).

## Testing

- Unit tests with the current JUnit and a mocking library used sparingly; assertions
  with a fluent library; parameterized tests for tables. Integration tests use real
  dependencies in containers rather than in-memory look-alikes. Slice tests for web
  and persistence layers keep suites fast. Property tests for pure logic; mutation
  testing on changed code (see `testing-strategy`).

## Container recipe

- Build the artifact in a build stage with the wrapper script; cache the dependency
  directory with a BuildKit cache mount; **use a layered jar or the build plugin's
  layering** so dependencies, the framework loader and your code are separate image
  layers, and a code change rebuilds only the last small one.
- Run on a minimal runtime image (a JRE-only or jlink-reduced base) as a numeric
  non-root user. Give the JVM the container limit: use percentage-based heap sizing
  (leave room for off-heap, threads and metaspace; do not give the heap all the
  memory), and set the CPU count the runtime sees.
- Exec-form entrypoint so the JVM is process 1 and gets SIGTERM; enable graceful
  shutdown in the framework with a timeout shorter than the pod's grace period; use
  the framework's liveness and readiness endpoints (liveness without dependency
  checks; see `kubernetes`).
- For fast start-up consider class-data sharing or an ahead-of-time image, and
  measure before committing (see `performance`).

## Security

- Parameterized queries; validate and encode output; no native deserialization of
  untrusted data; keep the framework and dependencies patched (see
  `dependency-management`); secrets from the environment or a manager.
