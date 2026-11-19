---
name: lang-typescript-react
description: React and TypeScript project setup and quality gates (Vite, strict tsconfig, ESLint flat config, Vitest, React Testing Library, Playwright). Use when creating, changing, reviewing or testing React or TypeScript front-end code.
verified: 2026-11-07
---

# React and TypeScript

## Current versions

Look these up when you start, never from memory: `npm view <package> version`
for react, typescript, vite, vitest, eslint and @playwright/test. Node.js: the
release feed `https://endoflife.date/api/nodejs.json`. Pick the Node line that
is in active LTS support, as its release schedule states.

## Setup

- Do not start new projects with Create React App. Use Vite with
  `@vitejs/plugin-react`, or Next.js if the app needs server rendering.
- Enable `"strict": true` in `tsconfig.json`. Keep a separate tsconfig for
  Node-side config files such as `vite.config.ts`.
- Pin the Node version (`.nvmrc` or `engines`) and commit the lock file
  (`package-lock.json`, `pnpm-lock.yaml` or `yarn.lock`, one per project).
- Keep secrets out of the client bundle. Anything the browser downloads is public.

## Quality gates

1. `tsc --noEmit` (type check)
2. ESLint with the flat config (`eslint.config.js`), including the React hooks
   rules.
3. `vitest run` for logic and hooks.
4. React Testing Library for components: test what users see and do.
5. Playwright for critical end-to-end flows, run against a built app or staging.

## Structure

- `src/` with feature folders; shared UI in one place; no cross-feature imports
  except through a public index file.
- Test files next to the code they test, or under `tests/` if the team prefers.

## Common mistakes

- Using `any` to silence a type error instead of fixing the type.
- Effects that fetch data without cleanup or cancellation.
- Testing implementation details (internal state) instead of behaviour.

Source to check before relying on details: the React, Vite, typescript-eslint,
Vitest and Playwright documentation.

## Deeper guide

`references/idioms.md` covers how this language handles errors, concurrency,
configuration, logging, testing, security and the container image, and where it
differs from the others. Read it when you design or review more than a small edit.
