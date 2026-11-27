---
name: performance
description: "Fix performance by measuring first: budget, profiling, biggest cost, careful caching, regression guards. Use when something is slow, before optimizing, when adding a hot path or cache, or reviewing a performance claim."
verified: 2026-11-19
---

# Performance

Measure, do not guess. Most code is fast enough; a few places are not, and
intuition about which is usually wrong.

## Rules

1. **Say what "fast enough" means** before you start: a target for a high
   percentile of latency, throughput, memory or start-up time, for a named
   workload. No target means no stopping point.
2. **Measure a baseline** with realistic data and load, on a machine and settings
   you can repeat. Record the numbers in the task.
3. **Profile to find the real cost.** Use a profiler, query plans and traces.
   Speeding up a part that is a small share of the time cannot give more than that
   share back.
4. **Fix the biggest cost first,** and usually in this order: unnecessary work,
   the algorithm or data structure, the number of round trips and queries, then
   memory and allocation, and only last micro-tuning.
5. **Change one thing, measure again,** keep it only if it helps. Keep before and
   after numbers in the pull request.
6. **Common database causes:** repeated queries in a loop (N+1: batch or join),
   missing or unused indexes (read the query plan), fetching more rows and
   columns than needed, no pagination, long transactions. Test on production-sized
   data.
7. **Common service causes:** chatty calls between services, no timeouts or pool
   limits, blocking calls on an async path, serial work that could run
   concurrently, large payloads, unbounded memory growth.
8. **Common front-end causes:** large bundles, render-blocking resources,
   unoptimized images, long main-thread tasks, needless re-rendering.
9. **Cache last, and with a plan.** A cache hides a bad access pattern and adds
   staleness. Before adding one, answer: can the work be made cheaper without it,
   how often does the data change, what does stale data cost, how is it
   invalidated, what happens on a cold cache and a stampede (many misses at once)?
   Bound its size and give it an expiry.
10. **Do not trade correctness, safety or readability for speed** unless the
    measurement demands it; then comment why and add a test that protects the
    behaviour.
11. **Guard it:** keep a benchmark or a load test for each budgeted path and run
    it in CI or on a schedule, watching the trend with enough runs to see through
    noise. Alert on production latency (see `observability`).

## Reporting a result

Write: workload, baseline, change, new number, how it was measured, and any cost
(memory, complexity, staleness). A claim without numbers is an opinion.

## Related

`observability`, `resilience`, `database-migrations` (indexes), `testing-strategy`.
