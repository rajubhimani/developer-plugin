---
name: repo-api-and-ui
description: "Work across an API repo and a UI repo: contract-first OpenAPI, generated clients, versioning, contract tests, browser end-to-end tests. Use when changing an API a front end uses, or setting up their repos and tests."
verified: 2026-11-07
---

# API repo and UI repo

Sources checked 2026-11-07 are secondary (vendor and community guides). Confirm
OpenAPI and Pact details against their official docs before relying on them.

## Contract first

- The API's OpenAPI document is the contract. Write or change it first, review
  it, then implement.
- Generate the UI's API client from that document. Do not hand-write request
  types that can drift from the server.
- Keep the spec in the API repo, versioned with the code. The UI repo pins which
  spec version it was built against.

## Compatibility rules

- **Non-breaking** (safe to ship): add an optional field, add an endpoint, add an
  enum value only if clients ignore unknown values.
- **Breaking** (needs a new version or a deprecation period): remove or rename a
  field, change a type, make an optional field required, change the meaning of a
  status code.
- Deprecate first, announce a date, then remove. Keep old behaviour until the
  consumers have moved.

## Contract tests

- Provider checks: the API's tests validate responses against the OpenAPI spec.
- Consumer-driven tests (for example Pact): the UI publishes the requests it
  makes and the responses it needs; the API verifies them in its CI before a
  release. This catches breaking changes that a spec alone misses.

## UI repo

- Read the API base URL from configuration per environment. Never hard-code it.
- No secrets in the browser bundle. Tokens are short-lived and stored as the
  platform recommends.
- End-to-end tests (Playwright) against a staging deployment for the main user
  flows; unit and component tests for the rest.
