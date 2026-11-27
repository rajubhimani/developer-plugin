---
name: error-handling
description: "Detect, classify, propagate, report and test errors without hiding them or leaking internals. Use when writing code that can fail, adding try or catch or error returns, designing error messages, or reviewing swallowed errors."
verified: 2026-11-19
---

# Error handling

An error you hide becomes a bug in another place. Decide for each failure who
can act on it, and tell them clearly.

## Rules

1. **Fail fast and loud at the source.** Check inputs at the boundary and return
   a clear error at once. Do not carry a bad value deeper.
2. **Never swallow an error.** An empty catch, or an ignored return value, is a
   defect. If you truly ignore one, say why in a comment.
3. **Handle it where you can act, otherwise pass it up** with context. Do not
   catch only to log and rethrow; that logs one failure many times.
4. **Add context, keep the cause.** Wrap with what you were doing ("loading
   invoice 42") and keep the original error attached.
5. **Separate kinds of failure:**
   - *Caller mistake* (bad input, not found, not allowed): tell the caller what
     to fix. Not retryable.
   - *Transient* (timeout, rate limit, lock): may be retried (see `resilience`).
   - *Bug or broken invariant:* stop the work, alert, fix. Do not continue.
6. **Use the language's normal mechanism** (exceptions, result types, error
   values) and be consistent in one codebase. Do not mix styles in one layer.
7. **Typed errors for what callers branch on;** plain messages for the rest. Give
   errors a stable code that does not change when wording changes.
8. **No internals to outsiders.** Responses and user messages carry no stack
   trace, query, path, host name or secret. Log the detail, return a safe
   message and a reference id.
9. **Clean up always** (close files, release locks, roll back) with the
   language's guaranteed mechanism (finally, defer, context manager, RAII).
10. **Do not use errors for normal flow,** and do not return a magic value
    (null, minus one, empty string) where an error belongs.
11. **Be careful at process edges.** A top-level handler logs once, returns a
    non-zero exit or a safe response, and never leaves a half-done write.

## Messages

State what happened, what was expected and what to do next. Include the offending
value only if it is safe to show. "Port must be between 1 and 65535, got 70000"
beats "invalid config".

## Test the failure paths

For each rule above that applies, a test: the bad input, the dependency that
times out, the error that must not leak. See `testing-strategy`.

## Related

`resilience` for retries and timeouts, `observability` for logging errors,
`api-design` for error responses, `security-review` for what must not leak.
