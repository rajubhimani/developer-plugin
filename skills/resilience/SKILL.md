---
name: resilience
description: Making calls between services and to dependencies safe to fail, with timeouts, bounded retries with backoff and jitter, idempotency, circuit breakers, bulkheads, graceful degradation and load shedding. Use when code calls a network service, queue or database, or when reviewing reliability.
verified: 2026-11-19
---

# Resilience

Every remote call will one day be slow, fail or repeat. Design for that before it
happens.

## Rules

1. **Every remote call has a timeout,** shorter than the caller's own deadline.
   No timeout means one slow dependency stops everything. Pass a deadline down
   the call chain.
2. **Retry only what is safe and transient.** Timeouts, connection resets and
   throttling may be retried. Bad input and "not allowed" may not.
3. **Bound retries:** a small maximum, exponential backoff, and random jitter so
   clients do not retry together. Respect a server's retry-after hint. Retry at
   one layer only; stacked retries multiply load.
4. **Make writes idempotent before you retry them.** Use an idempotency key (the
   server stores the first result and returns it for a repeat), a natural unique
   key, or a conditional write. A retried payment must not charge twice.
5. **Circuit breaker for a failing dependency:** after a failure rate or latency
   threshold, stop calling for a while, then probe. Retries stop while open.
6. **Isolate with bulkheads:** separate pools or limits per dependency so one
   slow service cannot use every thread or connection.
7. **Degrade on purpose.** Decide the fallback in advance: cached data, a default,
   a reduced feature, a clear "try later". Do not fail the whole page for one
   widget.
8. **Limit work you accept:** bounded queues, request size limits, rate limits,
   and load shedding (refuse early with a clear error) over unbounded buffering.
9. **Process messages at least once,** so handlers must tolerate duplicates and
   out-of-order delivery. Use a dead-letter queue for poison messages, with an
   alert.
10. **Shut down cleanly:** stop taking work, finish or hand back in-flight work,
    then exit, within a time limit.
11. **Health checks tell the truth:** liveness (process is stuck) apart from
    readiness (can serve now). A dependency being down is a readiness matter, not
    a reason to restart.
12. **Test failure.** Inject timeouts, errors and duplicates in tests; for
    critical paths, rehearse in a staging environment.

## Numbers

Timeouts, retry counts and thresholds depend on the service. Start from measured
latency (a high percentile, not the average) and revise from production data.
Treat any example number in a guide as a starting point.

## Related

`error-handling`, `observability` (watch retry and breaker rates), `api-design`
(idempotency keys), `concurrency`.
