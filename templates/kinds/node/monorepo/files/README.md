# {{title}}

<one line: what this repository holds>

```text
apps/       deployable things; nothing depends on them
packages/   shared code: ui components, utilities, shared configuration
docs/       architecture and decisions
```

## Work in it

```bash
pnpm install               # one lock file for every member
pnpm --filter <member> test   # one member
make check                 # type-check, lint, test everything
```

Members and the dependency rules are in [docs/architecture.md](docs/architecture.md); the
rules are enforced by `make structure-check`.

> **Lint and the newest TypeScript.** The lint plugin (`typescript-eslint`) can lag a new
> TypeScript major release. If `lint` says your TypeScript version is not supported,
> install the newest TypeScript release the plugin supports (its documentation lists
> the range), for example `pnpm add -D typescript@<supported-major>`.

Dependencies are not pinned in these templates. Add the current versions with
`pnpm add` (see each member's README). When CI time becomes the problem, add a task
runner with caching (such as Turborepo) on top of this layout; the layout does not change.
