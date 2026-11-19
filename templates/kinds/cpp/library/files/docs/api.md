# Public API

The public API is the headers under `include/{{package}}/` and nothing else; files under
`src/` are private.

| Item | Since | Notes |
|---|---|---|
| `{{package}}::greet(name)` | 0.1.0 | Returns a greeting; throws `std::invalid_argument` for an empty name |

## Rules for changing it

- **Add** an item: a minor version; document what it throws and who owns what it returns.
- **Change** a signature, a class layout or an exception type: a major version (the binary
  interface changes too).
- **Remove** an item only in a major version, after marking it `[[deprecated("use X")]]` for
  one minor release so the compiler warns.
