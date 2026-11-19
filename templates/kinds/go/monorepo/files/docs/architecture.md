# Architecture

## Layout

```text
go.work               the workspace (`use` lists every member)
apps/<member>/        a service or command: its own module, cmd/ and internal/
packages/<member>/    a library: its own module and public API
```

Module paths follow the folders: `{{module}}/apps/<member>` and
`{{module}}/packages/<member>`.

## Dependency rules (checked by `make structure-check`)

1. `apps/*` may import `packages/*`.
2. `packages/*` never import `apps/*`.
3. An app never imports another app. Shared code moves down into a package.
4. Declare a sibling in the member's `go.mod` (`require {{module}}/packages/core v0.0.0`);
   `go.work` resolves it locally. Do not commit `replace` directives.
5. Import only a package's exported API; code that is private to a member lives under
   its own `internal/`.
6. Every member has its own tests and README.

## Versions

Apps are deployed, not versioned for others. A library that other repositories import is
tagged per module (`packages/core/v1.2.0`); a new major version changes its module path.
Libraries used only inside this repository need no tag.

## Ownership

`.github/CODEOWNERS` names who reviews each folder. Shared packages get the strictest
review.

## CI

Test every module; once the repository is large, test only modules that changed and the
modules that depend on them (see the repo-layout and ci-cd skills).

## Members

| Member | Kind | Purpose |
|---|---|---|
{{member_rows}}
