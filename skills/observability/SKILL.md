---
name: observability
description: "Logs, metrics, traces, alerts, redaction. Use when adding monitoring, or a production failure is hard to diagnose."
metadata:
  verified: "2026-11-19"
---

# Observability

You cannot fix what you cannot see. Build the questions you will ask at 3 a.m.
into the code: what failed, for whom, where, and since when.

## Three signals

- **Logs:** discrete events with detail. Good for "what happened to this request".
- **Metrics:** numbers over time. Good for "is it healthy, is it getting worse".
- **Traces:** one request across services. Good for "where did the time go".

Use one standard (OpenTelemetry is the common open one) so signals link up and
you are not tied to one vendor. Look up its current setup for your language.

## Logging rules

1. **Structured, one event per line,** key and value (JSON), with a stable
   message and the variable parts in fields, not glued into the text.
2. **Standard fields:** time (UTC), level, service, version, environment, and the
   trace and span ids so a log line joins its trace. Use the trace context that
   propagates between services before inventing your own id.
3. **Levels mean something:** *error* needs a person or a fix, *warn* is
   unexpected but handled, *info* is a business or lifecycle event, *debug* is
   off in production by default. A log that always fires with no action is noise.
4. **Log once where it is handled,** not at every layer it passes (see
   `error-handling`).
5. **Never log secrets or raw personal data:** tokens, passwords, keys, full card
   numbers, health or identity data. Log ids, not content. Redact at the logger
   and at the collector so one mistake does not leak. Do not log whole request
   bodies or headers by default.
6. **Treat logged input as hostile:** it can contain newlines and control
   characters meant to forge entries. Encode it (see `untrusted-input`).
7. **Keep volume and cost in check:** sample high-volume debug events, set
   retention, and never log inside a hot loop.

## Metrics rules

1. For each service watch **rate, errors and duration** of requests, and for each
   resource **utilisation, saturation and errors**.
2. Use percentiles for latency (a high one), not just the average.
3. **Keep label values few.** An id, email or URL path with ids as a label makes
   the series count explode.
4. Add business metrics (orders placed, jobs failed) beside technical ones.

## Tracing rules

Propagate context across every hop, including queues and background jobs. Name
spans by operation, not by data. Add the key attributes (route, status, result),
no secrets.

## Alerts

Alert on **symptoms users feel** (error rate, latency, failed jobs, a saturated
resource that will page soon), not on every cause. Each alert has an owner, a
link to a runbook, and a reason it needs a human now; delete alerts nobody acts
on.

## Before shipping a change

State how you will know it works and how you will know it broke: which log, which
metric, which dashboard or alert. The deploy review asks for this (see
`ci-cd`, `debug-failure`).
