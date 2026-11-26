---
name: concurrency
description: Correct concurrent and async code: shared state, locks, cancellation, deadlines, structured concurrency, race tests. Use when adding threads, async tasks, background jobs, caches or locks, or debugging flaky or hung behaviour.
verified: 2026-11-19
---

# Concurrency

Most concurrency bugs come from shared mutable state. The best fix is to not
share it.

## Rules

1. **Do you need it?** Concurrency adds bugs that are hard to reproduce. Use it for
   I/O waiting or independent heavy work, not by habit.
2. **Do not share mutable state.** Prefer, in order: immutable data, passing
   messages between workers (each owns its data), one owner per piece of data,
   then locks.
3. **If you share, protect every access** with the same lock or an atomic type,
   for reads as well as writes. Keep critical sections tiny and never call unknown
   code or do I/O while holding a lock.
4. **Avoid deadlock:** take locks in one global order, hold few at a time, and use
   timeouts where the language allows.
5. **Check-then-act is a race.** "If not exists, then create" needs one atomic
   step: a lock, a unique constraint, or a conditional write.
6. **Keep async code non-blocking.** Do not run blocking calls or long CPU work on
   an event loop; hand them to a worker pool. Never forget to wait for a started
   task; an unawaited task loses its errors.
7. **Structured concurrency:** start tasks inside a scope that waits for them all,
   so no task outlives its parent and errors reach the caller. Prefer it to loose
   "fire and forget".
8. **Cancellation and deadlines are cooperative.** Pass a cancellation signal or
   deadline down the call chain, check it at I/O and between long steps, and clean
   up when cancelled. A task you cannot cancel is a leak.
9. **Bound everything:** worker counts, queue lengths and in-flight requests, with
   back-pressure instead of unbounded buffers (see `resilience`).
10. **Make background work idempotent and restartable,** because it will run twice
    or stop half way.
11. **Per-request state stays per request.** Beware shared globals, caches without
    locks, and module-level mutable defaults.
12. **Order is not guaranteed** unless you build it; do not rely on timing or on
    sleeps.

## Test

- Run the suite with the language's race detector or thread sanitizer where one
  exists, in CI.
- Stress the code: many repeats, many workers, injected delays.
- Wait on conditions or events, not fixed sleeps; async waiting is the usual cause
  of flaky tests (see `testing-strategy`).
- A test that passes only sometimes is a bug report, not noise.

## Related

`resilience`, `error-handling`, `debug-failure`, language skills for the race
tools.
