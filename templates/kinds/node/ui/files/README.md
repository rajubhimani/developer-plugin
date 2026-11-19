# {{name}}

Shared React components.

- Export every public component and its props type from `src/index.ts` only.
- Use native elements and keep keyboard and screen reader behaviour (see the
  accessibility skill). Test components by role and text, not by implementation.
- Keep this package free of app logic and of imports from any app.
- Add the tools with your package manager: `pnpm add -D typescript vitest eslint
  @eslint/js typescript-eslint @testing-library/react @types/react jsdom`.
