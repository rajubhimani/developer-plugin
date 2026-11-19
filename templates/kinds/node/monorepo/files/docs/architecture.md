# Architecture

## Layout

```text
apps/<member>/        deployable: a web app or service
packages/<member>/    shared: ui components, utilities, configuration
pnpm-workspace.yaml   lists the member folders
pnpm-lock.yaml        the only lock file
```

Members are named `@{{scope}}/<member>`.

## Dependency rules (checked by `make structure-check`)

1. `apps/*` may depend on `packages/*`.
2. `packages/*` never depend on `apps/*`.
3. An app never depends on another app. Shared code moves down into a package.
4. Depend on a sibling with the workspace protocol, so the local copy is always used:

   ```json
   "dependencies": { "@{{scope}}/ui": "workspace:*" }
   ```
5. Import a package only through its entry point (the `exports` map); never reach into
   its `src/` folder.
6. Every member extends the shared TypeScript settings in `packages/config`.
7. One purpose per package; do not nest packages inside packages.

## Internal packages

Packages used only inside this repository export their TypeScript source
(`"exports": { ".": "./src/index.ts" }`), so there is no build step to keep in sync.
A package that is published gets its own build and the standalone library layout.

## Ownership

`.github/CODEOWNERS` names who reviews each folder. Shared packages get the strictest
review: a break there reaches every app.

## Versions

Apps are deployed, not versioned for others. Published packages are versioned
independently with semantic versions and a changelog each. Share external dependency
versions in one place (the workspace catalog) instead of repeating them.

## CI

Build and test what changed and what depends on it (see the repo-layout and ci-cd
skills). While the repository is small, running everything on each pull request is the
simplest correct choice.

## Members

| Member | Kind | Purpose |
|---|---|---|
{{member_rows}}
