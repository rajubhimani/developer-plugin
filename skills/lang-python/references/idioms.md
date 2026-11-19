# Python idioms and how to handle common concerns

Python's strengths are readability, a large standard library and fast iteration.
Its costs are runtime errors, a global interpreter lock for threads and loose
typing unless you add it. These practices keep the strengths and cover the costs.

## Types

- Annotate every public function, and run the strict type checker (see the main
  skill). Use built-in generics (`list[str]`), `X | None`, `Protocol` for
  structural interfaces, `TypedDict` for dictionary shapes and `NewType` for ids
  that must not be mixed up.
- **Dataclasses for internal data** (`frozen=True`, `slots=True`), **pydantic
  models for data from outside** (HTTP bodies, files, environment). Validate once
  at the boundary, pass typed objects inward.
- Do not use mutable default arguments. Use `None` and create inside, or
  `field(default_factory=...)`.

## Errors

- Catch specific exceptions. Never a bare `except:`; a broad `except Exception`
  only at a process or request edge that logs and returns a safe answer.
- Re-raise with context: `raise NewError("loading invoice 42") from exc`.
- Define a small base exception per package and subclass it for failures callers
  branch on. Give each a stable code.
- Use `ExceptionGroup` and `except*` when several tasks fail together.
- Do not use `assert` for input checks; it can be disabled. Raise a real error.
- Use context managers (`with`) for files, locks, connections and transactions so
  cleanup always runs.
- Return or raise; do not return `None` to mean "failed". See `error-handling`.

## Configuration

- One `Settings` class (pydantic-settings) with typed fields and defaults for
  non-secrets. Order of sources: explicit arguments, real environment variables,
  `.env` file, mounted secret files, defaults. Real environment wins.
- Give secrets the secret type so they print as stars, and never log the settings
  object whole.
- Create settings once at start-up (a cached function), pass them in, do not read
  the environment deep in the code. Forbid unknown keys where you can.
- See `containers.md` for how the same names flow through Compose and Kubernetes.

## Logging

- Use the standard `logging` module or a structured logger; no `print`. One
  logger per module (`logging.getLogger(__name__)`).
- JSON lines to standard output in production, readable console output locally,
  chosen by a setting. Bind request and trace ids once per request with context
  variables so every line carries them (see `observability`).
- Pass values as fields, not by string formatting into the message. Never log
  secrets or personal data.

## Async and concurrency

- Threads share the interpreter lock, so they help with waiting on I/O, not with
  CPU work. For CPU-bound work use processes (or a native extension). Look up the
  current state of free-threaded builds before relying on them.
- In async code never call blocking functions on the event loop; move them to a
  thread with `asyncio.to_thread` or use an async client.
- Put a timeout on every awaited call (`asyncio.timeout`).
- Start related tasks in a `TaskGroup` so errors propagate and nothing is left
  running. Never swallow `CancelledError`; clean up and re-raise.
- Keep references to tasks you create, or the loop may drop them.
- Bound concurrency with a semaphore or a queue with a maximum size.
- Share nothing mutable between tasks without a lock (see `concurrency`).

## Data and resources

- Use `pathlib`, not string paths. Use generators and iterators for large data;
  do not build huge lists. Use `with open(...)` and name the encoding.
- Prefer the standard library and the frameworks already in the project before
  adding a package (see the main skill, "Reuse before writing").
- Use `functools.cache` only for pure functions with bounded inputs; an unbounded
  cache is a memory leak (see `performance`).
- Do not do work at import time (network, files, heavy computation). It slows
  start-up and breaks tests.

## Testing

- `pytest` with plain functions and fixtures; `parametrize` for tables of cases;
  `tmp_path` for files; `monkeypatch` for settings and environment.
- Inject the clock, randomness and clients as arguments or fixtures, so tests need
  no patching of internals. No real network or real time.
- Test the public behaviour; use a fake for a port and the real thing in a few
  integration tests (a throwaway database in a container is fine).
- Property tests (Hypothesis) for parsers, calculations and round trips. See
  `testing-strategy`.
- Async tests use the project's async plugin; do not sleep, wait on events.

## Security

- Never `pickle` or `yaml.load` untrusted data; use safe loaders and data formats.
- `subprocess` with an argument list, never `shell=True` with user text. Avoid
  `eval` and `exec`.
- Parameterize SQL; never format values into queries. Use `secrets` for tokens,
  not `random`.
- Resolve and check user-supplied paths against a base directory; never trust
  file names.
- Audit dependencies and keep the lock current (see `dependency-management`).

## Performance

- Profile first (the built-in profiler, a sampling profiler that attaches to a
  running process). Typical wins: fewer queries, the right data structure,
  vectorized numeric code (see "Reuse before writing"), moving work out of loops.
- Use `__slots__` or dataclass slots for many small objects, generators for
  streams, and measure before and after (see `performance`).

## Web services

- Pick one framework per service, keep handlers thin (parse, call a function,
  return), and keep domain logic in plain functions you can test without the
  framework.
- Use dependency injection the framework offers for settings and clients.
- Return problem-details errors (see `api-design`). Add request-id middleware.
- Run migrations as a separate step, not on every start (see
  `database-migrations`).
