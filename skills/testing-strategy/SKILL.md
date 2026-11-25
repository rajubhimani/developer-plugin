---
name: testing-strategy
description: How many tests and where, test-first order, honest tests, small reliable suites. Use when planning tests for a change, writing a failing test first, or reviewing whether tests guard behaviour.
verified: 2026-11-17
---

# Testing strategy

Language skills say which tools to use. This skill says what to test and how
to keep the tests honest.

## Scale tests to the damage a bug can do

Score the requirement on three points: how far a wrong result spreads, how hard
it is to undo, and how long it stays hidden. A silent, irreversible, wide-reaching
bug deserves the most tests; a loud, local, revertable one deserves one.

| Damage | Tests |
|---|---|
| Trivial | None for that example; state why in the change |
| Contained | One test at the public boundary |
| Serious | Two or three, one of them a failure case |
| Severe | As serious, plus a property test and a mutation check on the changed lines |

A change that alters behaviour always gets at least one test. Text another
program reads (a JSON key, an error code, output format) is a contract and
counts as behaviour. Doc-only, config-only and wording-only changes get review
instead.

## Order

1. Write the test first and run it. It must fail, and for the right reason: on
   its assertion, not on an import error or a typo.
2. Commit the failing test (or at least keep it separate in your notes), then
   make it pass, then refactor with the test green.
3. Do not edit the test to make the change pass. If you think the test is wrong,
   say so and ask; do not change it quietly.

## Rules

- Test observable behaviour at the public boundary, not internals. If a correct
  rewrite would force the test to change, it tests mechanics.
- Tests are deterministic: fixed clocks, seeded randomness, no network, no
  order dependence.
- Where inputs vary, prefer a property over one example; a builder cannot
  hard-code inputs it never sees.
- Do not target a coverage percentage. It rewards lines run, not behaviour
  checked.
- Every test costs runtime, upkeep and a chance of a spurious failure. A suite
  of thousands with even a tiny flake rate fails often. Keep suites small and
  weighted by risk, and delete a test that duplicates a stronger one, asserts
  an internal detail, or has never caught anything.
- Fix a flaky test or remove it. Never rerun until green.

## Check that a test can fail

- Delete or invert one guarded clause in a copy outside the working tree and
  confirm a test goes red. Say in your report that you did this.
- Look for signs of gaming: literals from test fixtures inside production code,
  branches keyed on test inputs, results returned as the expected value,
  skipped or focused tests, removed assertions.
- A green unit suite does not prove a screen, a deploy or a script works. Run
  the real thing once and record the command and what you saw.

## Stronger techniques, used where they pay

- **Property-based tests** state a rule that must hold for all valid inputs and
  let a tool generate the cases and shrink a failure to a small one. Use them for
  parsers, calculations, encoders, state machines and anything with an inverse.
  Plain create-and-read code has no interesting property; use examples. Run fewer
  cases locally and more in CI, and keep the seed of a failing run.
- **Mutation testing** changes the code in small ways and checks that a test
  fails. A surviving mutant means a weak assertion or a missed boundary. It is
  slow, so run it on changed code in a pull request or on a schedule, not on every
  save, and use it to find gaps, not as a score to chase.
- **Contract tests** let a consumer and a provider check compatibility without
  running both together (see `repo-api-and-ui`, `api-design`).
- **Characterization tests** record what legacy code does before you change it
  (see `refactoring`).
- **Failure tests:** timeouts, duplicates, bad input and the error that must not
  leak (see `error-handling`, `resilience`).
- **Flaky tests:** the usual cause is waiting on time instead of a condition, then
  shared state, order dependence and real clocks or networks. Wait on an event,
  isolate state, fix the clock. See `concurrency`.

