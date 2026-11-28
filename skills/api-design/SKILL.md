---
name: api-design
description: "API design: naming, status codes, error format, pagination, idempotency, versioning. Use when adding or changing an endpoint or public function."
metadata:
  verified: "2026-11-19"
---

# API design

An API is a promise to people you cannot see. Make it boring and predictable, and
change it without breaking them. Write the contract first (see `repo-api-and-ui`).

## HTTP rules

1. **Resources are nouns, methods are verbs.** Plural collections and ids in the
   path; actions that do not fit a resource get a clear sub-resource or an
   explicit action endpoint.
2. **Use methods and codes for what they mean.** Safe methods change nothing.
   Create returns the created status with the new resource's location. Use the
   client-error codes (bad request or unprocessable, unauthorized, forbidden, not
   found, conflict, too many requests) and server-error codes in a consistent way
   across the whole API, and document the choice once.
3. **One error format.** Use the standard problem-details shape (media type
   `application/problem+json`): `type`, `title`, `status`, `detail`, `instance`,
   plus fields you add, such as per-field validation errors and a stable error
   code. No stack traces, queries or other internals (see `error-handling`,
   `security-review`).
4. **Paginate every list.** Prefer cursor pagination for large or changing data
   (stable under inserts, no deep-offset cost); offset is fine for small bounded
   sets. Return the next link or cursor, set a default and a maximum page size,
   and give a stable sort order.
5. **Filter, sort and select with named parameters** that are validated against
   an allow-list. Reject unknown ones rather than ignoring them silently.
6. **Idempotency.** Reads, replaces and deletes are idempotent by design. For
   creates and other unsafe calls that clients may retry, accept an
   `Idempotency-Key` header: store the first result under the key for a limited
   time and return it on a repeat; reject the same key with a different body (see
   `resilience`).
7. **Concurrency control:** use an entity tag with a conditional update to stop
   lost updates.
8. **Validate every input at the edge** with an allow-list, size limits and types.
   Authenticate and authorize on every request, at the object level too, not just
   the route (see `security-review`).
9. **Rate limit and say so** with a retry hint in the response.
10. **Consistent shapes:** same names, same date format (UTC, ISO form), money as
    an integer minor unit plus currency, ids as opaque strings.
11. **Long work:** return an accepted status and a status resource to poll, or a
    callback, not a request that hangs.

## Compatibility and versioning

- **Additive changes are safe:** new optional fields, new endpoints, new enum
  values *if* clients were told to tolerate unknown ones.
- **Breaking:** removing or renaming a field, changing a type or meaning, making
  an optional input required, tightening validation. Add a new version or, better,
  expand then contract: add the new, support both, deprecate the old with a date
  and a header, remove after the notice period (see `versioning-release`).
- **Be liberal in what you read, strict in what you write.**
- **Consumer-driven contract tests** show which clients a change would break
  before release.

## Library and function APIs

Small surface, hard to misuse, errors in the types, no boolean flag arguments that
change meaning, document each public item with an example, and deprecate before
removing.

## Related

`repo-api-and-ui`, `error-handling`, `resilience`, `security-review`.
