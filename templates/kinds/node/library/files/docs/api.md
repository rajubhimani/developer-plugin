# Public API

Only what `src/index.ts` exports is public. The `exports` map in `package.json` allows
no other entry point, so deep imports into `dist/` are not supported.

| Name | Kind | Since | Notes |
|---|---|---|---|
| `greet(name)` | function | 0.1.0 | Returns a greeting; throws for an empty name |

## Rules for changing it

- **Add** an export: a minor version; add it to this table and a test.
- **Change** behaviour or a signature that callers notice: a major version, after a
  deprecation period of at least one minor release.
- **Remove** an export only in a major version.
