# TypeScript and React idioms and how to handle common concerns

TypeScript's strengths: types over a huge ecosystem, one language front and back.
Its costs: types are erased at run time, so data from outside is unchecked until you
check it, and bundle weight grows quietly.

## Types

- Strict mode on. No `any`; use `unknown` and narrow. No non-null assertions or type
  casts to silence an error; fix the type.
- **Validate data at the boundary** (API responses, form input, storage, URL
  parameters) with a schema library and derive the type from the schema, so the
  type is true at run time.
- Discriminated unions for states (`loading | error | ready`) and exhaustive
  matching, instead of several booleans.
- Prefer `readonly` and immutable updates. Use `satisfies` and literal types to
  keep precision. Brand ids that must not be mixed.

## Errors

- Throw `Error` objects (subclasses for kinds callers branch on); never throw
  strings. Keep the `cause`.
- Handle every promise: `await` it or attach a catch. An unhandled rejection is a
  bug. Never an empty catch.
- Return typed result values where failure is expected and local; throw for the
  unexpected.
- In React, use error boundaries around routes and widgets, show a useful message
  and a retry, and report the error (see `error-handling`, `observability`).
- Network calls have timeouts and cancellation (`AbortController`), retries only
  for safe requests (see `resilience`).

## React

- Components are small, pure and typed; state lives as low as possible; derive
  values instead of storing them. Do not mirror props into state.
- **Server state is not client state.** Use a data-fetching cache for server data
  (loading, errors, retries, invalidation) and keep local state for the interface.
- Effects are for syncing with the outside world, not for computing values or
  responding to events. Clean up every subscription and timer. List every
  dependency (the lint rule enforces it).
- Stable keys in lists; never use the index when order can change.
- Memoize only after measuring. Split code by route and lazy-load heavy parts.
- Forms: controlled or a form library; validate with the same schema as the API;
  accessible labels and errors (see `accessibility`).

## Concurrency and async

- The runtime is single-threaded: use `Promise.all` for independent work and a
  limit for many. Do not block the main thread with long loops; use a worker for
  heavy work.
- Cancel stale requests (latest wins); avoid race conditions between responses.
- In Node services, never block the event loop with sync file or CPU work on a hot
  path.

## Configuration

- **Server code** reads the environment once at start-up into a validated typed
  object; fail fast; the environment wins over a local `.env` (see
  `secrets-and-config`).
- **Browser code cannot hold secrets or read the runtime environment.** Build-time
  variables are compiled into the bundle and public. For one image across
  environments, load a small runtime config file (served at start-up from the same
  ConfigMap) instead of baking values in (see `kubernetes` `config-flow.md`).

## Testing

- Unit tests with the project's runner; component tests with Testing Library,
  querying by role and text as users do, not by implementation details. Mock the
  network at the boundary with a mock server. A few end-to-end tests of the critical
  flows in a real browser. Contract tests against the API (see `api-design`).
- Accessibility checks in component tests (see `accessibility`). Avoid snapshot
  tests of large trees. No fixed sleeps; wait for conditions.

## Performance

- Measure with the browser's profiler and the framework's profiler; watch bundle
  size, long tasks and layout shifts. Compress and cache static assets with hashed
  names. Optimize images. Avoid heavy dependencies for small needs (see
  `dependency-management`, `performance`).

## Container recipe

- Node service: multi-stage; install from the lockfile with a cache mount for the
  package store; build; copy only the output and production dependencies; run as a
  non-root user; **exec-form command that starts the runtime directly,** not through
  a package-manager script, so SIGTERM reaches it. Handle SIGTERM: stop accepting,
  close the server, then exit after a timeout.
- Static front end: build in one stage, serve from a small web server image as
  non-root with a read-only filesystem and a writable temp path; set security and
  cache headers; inject the runtime config at start.
- Never copy `.env` or the source tree into the final image.

## Security

- Escape by default (the framework does); never insert raw HTML from users; if you
  must, sanitize with a vetted library. Set a content security policy. Keep tokens
  out of local storage where possible; prefer secure, same-site cookies.
- Treat every package install script and new dependency with care (see
  `dependency-management`).
