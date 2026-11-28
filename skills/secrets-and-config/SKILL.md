---
name: secrets-and-config
description: "Where config and secrets live, rotation, leaks. Use when deciding where a password, API key or token goes, or a secret may be exposed."
metadata:
  verified: "2026-11-19"
---

# Secrets and configuration

Configuration is what changes between deploys. A secret is configuration that
causes harm if it leaks. Treat the two differently.

## Configuration

1. **Keep config out of code** and apart from it: anything that differs per
   environment (addresses, flags, limits) is read at start-up from the
   environment, a file or a config service.
2. **Same build everywhere.** One artifact is promoted through environments; only
   the config changes (see `ci-cd`).
3. **Validate at start-up.** Parse every setting into a typed value, apply
   defaults in one place, and fail fast with a clear message when a required one
   is missing.
4. **Document each setting:** name, meaning, type, default, and whether it is a
   secret. Ship an example file with fake values.
5. **Feature flags are config too:** give each an owner and a removal date.

## Secrets

1. **Never in git, images, logs, error messages, client-side code or chat.** Not
   in an encrypted file next to the key either.
2. **Use a secrets manager** or the platform's secret store, and mount or inject
   at run time. Environment variables are a delivery method, not a safe; they can
   leak through process listings, crash dumps and child processes. Platform
   secrets may be only encoded, not encrypted, so restrict who can read them.
3. **Least privilege.** Each service gets only the credentials it needs, scoped
   to one environment and one action. Prefer short-lived credentials from workload
   identity over long-lived keys (see `ci-cd`).
4. **Rotate on a schedule and on demand,** and design for it: two valid keys
   during a changeover, no restart-only secrets, no copy kept in someone's notes.
5. **Separate environments:** production secrets are not on developer machines,
   and test data holds no real secrets or personal data.
6. **Scan for leaks:** a pre-commit and a CI scanner for secrets, with a block on
   findings (see `git-workflow`).

## If a secret leaks

Assume it is compromised the moment it is pushed or logged.

1. **Revoke or rotate it first.** Deleting the commit does not help; history,
   forks and caches keep it.
2. Check the provider's audit log for use since the leak.
3. Find and fix how it got out (a missing ignore rule, a debug log).
4. Rewriting history is a separate, optional clean-up that needs the owner's
   approval (see `git-workflow`).
5. Write a short note: what, when, impact, fix.

## Related

`security-review`, `observability` (redaction), `docker` (build secrets).
