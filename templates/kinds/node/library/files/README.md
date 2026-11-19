# {{name}}

<one line: what this library does and who it is for>

## Install

```bash
pnpm add {{name}}
```

## Use

```ts
import { greet } from "{{name}}";

console.log(greet("world"));
```

## Develop

Add the tools with your package manager (versions are not copied into this template):
`npm install -D typescript vitest eslint @eslint/js typescript-eslint` (or `pnpm add -D ...` in a workspace). Then `make check`.

> **Lint and the newest TypeScript.** The lint plugin (`typescript-eslint`) can lag a new
> TypeScript major release. If `lint` says your TypeScript version is not supported,
> install the newest TypeScript release the plugin supports (its documentation lists
> the range), for example `pnpm add -D typescript@<supported-major>`.

## Public API and versions

Only what `src/index.ts` exports is public; see [docs/api.md](docs/api.md). Versions follow
semantic versioning; every release is in [CHANGELOG.md](CHANGELOG.md).
