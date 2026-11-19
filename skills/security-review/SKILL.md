---
name: security-review
description: A security checklist for reviewing a diff or a design (secrets, injection, authorization, dependencies, logging, crypto, untrusted input). Use when reviewing a change that touches authentication, user data, secrets, external input, dependencies or deployment.
verified: 2026-11-17
---

# Security review

Map each item onto the project's real stack first. An item for something the
project does not use is not applicable, which is different from a pass.

## Checklist

| # | Confirm | How |
|---|---|---|
| 1 | No secret is hard-coded, including in tests and fixtures | Scan, then read each hit |
| 2 | No value is concatenated into a query, shell call or template; identifiers taken from input are checked against an allow-list | Read |
| 3 | Untrusted text is escaped before it reaches HTML, a template or a command | Read |
| 4 | Every new entry point states its authorization (or is explicitly public), checks the right user or role, and fails closed | Read |
| 5 | Data isolation between users or tenants holds at the layer this system uses | Read |
| 6 | Each new dependency was scanned or looked up by name and version; no advisory is invented | Run the scanner |
| 7 | Logs hold no password, token, full personal data or payment data | Read |
| 8 | Crypto uses the platform library, passwords use a current slow hash, tokens come from a secure random source | Read |
| 9 | Untrusted input never reaches a loader that can build arbitrary types | Read |
| 10 | Where untrusted text reaches a model prompt or tool call, instructions and data stay apart and model output is checked before it runs or renders (see `untrusted-input`) | Read |
| 11 | A change that removes or weakens a control other code relies on names what enforces it now | Read |
| 12 | A rollback or toggle on a sensitive path cannot leave a control off | Read |

## Reporting

- A finding blocks only with evidence: the file and line, the rule it
  contradicts, and the fix. Anything less is a note.
- Run exploit attempts on a copy outside the working tree.
- Say which items were not applicable and which could not be checked.
