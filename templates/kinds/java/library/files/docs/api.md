# Public API

The public API is the public types and members of `{{javapkg}}`; keep everything else
package-private.

| Item | Since | Notes |
|---|---|---|
| `Greeter.greet(String)` | 0.1.0 | Returns a greeting; throws for `null` or a blank name |

## Rules for changing it

- **Add** a type or method: a minor version; document it with javadoc (the build checks it).
- **Change** a signature, a thrown exception or behaviour callers rely on: a major version.
- **Remove** an item only in a major version, after annotating it `@Deprecated(since = "...",
  forRemoval = true)` and pointing to the replacement in the javadoc for at least one minor
  release.
