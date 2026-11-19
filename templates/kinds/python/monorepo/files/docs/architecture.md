# Architecture

## Layout

```text
apps/<member>/        deployable: a service or a command line tool
packages/<member>/    library: shared code with a small public API
pyproject.toml        workspace root: members, shared tool settings
uv.lock               the only lock file
```

Member names carry the repository name (`{{name}}-<member>`, imported as
`{{package}}_<member>`), so they never clash with a public package.

## Dependency rules (checked by `make structure-check`)

1. `apps/*` may depend on `packages/*`.
2. `packages/*` never depend on `apps/*`.
3. An app never imports another app. Shared code moves down into a package.
4. Import another member only through its public API (its package `__init__`), never
   a private module (one that starts with an underscore).
5. Declare every dependency on a sibling in that member's `pyproject.toml`:

   ```toml
   dependencies = ["{{name}}-core"]

   [tool.uv.sources]
   {{name}}-core = { workspace = true }
   ```

6. Tool settings (ruff, pyright, pytest) live in the root file only.
7. Every member has its own `tests/` folder and its own README.

## Ownership

`.github/CODEOWNERS` names who reviews each folder. Shared packages get the
strictest review: a break there reaches every app.

## Versions

Apps are deployed, not versioned for others. Packages that are published are
versioned independently with semantic versions and a changelog each. Packages used
only inside the repository need no release.

## CI

Run checks for what changed and for what depends on it (see the repo-layout and
ci-cd skills). Until the repository is large, `make check` on every pull request is
the simplest correct choice.

## Containers

Build a service image with the repository root as the build context so the lock
file and the sibling packages it needs are available, for example
`docker build -f apps/<member>/Dockerfile .`. Install with `uv sync --locked
--package <member>`; copy the lock file and each member's `pyproject.toml` first so
the dependency layer stays cached (see the lang-python skill).

## Members

| Member | Kind | Purpose |
|---|---|---|
{{member_rows}}
