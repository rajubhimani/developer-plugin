# {{title}}

<one line: what this app does>

## Set up

Dependencies are not pinned in this template; add the current versions with your
package manager so nothing is copied from memory (use `pnpm add` inside a pnpm
workspace, `npm install` in a standalone project):

```bash
npm install react react-dom
npm install -D vite @vitejs/plugin-react typescript vitest jsdom @testing-library/react \
  @types/react @types/react-dom eslint @eslint/js typescript-eslint
```

> **Lint and the newest TypeScript.** The lint plugin (`typescript-eslint`) can lag a new
> TypeScript major release. If `lint` says your TypeScript version is not supported,
> install the newest TypeScript release the plugin supports (its documentation lists
> the range), for example `pnpm add -D typescript@<supported-major>`.

## Develop

```bash
npm run dev       # local server with hot reload
make check        # type-check, lint, test, build
```

## Configuration

A browser bundle is public and cannot read a server's environment. Values compiled in
at build time are fixed in the build. To run one build in every environment, load a
small runtime config file at start-up instead of baking values in (see the kubernetes
skill, config-flow). Never put a secret in the bundle.
