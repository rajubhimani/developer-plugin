# Public API

The public API is the header `include/{{package}}/{{package}}.h` and nothing else; files
under `src/` are private.

| Function | Since | Notes |
|---|---|---|
| `{{package}}_greet(name, out, out_size)` | 0.1.0 | Writes a greeting; never writes past `out_size` |

## Rules for changing it

- **Add** a function: a minor version; document ownership, error codes and an example.
- **Change** a signature, a struct layout or the meaning of a result code: a major version.
  The binary interface changes too, so bump the library's shared-object version.
- **Remove** a function only in a major version, after marking it deprecated for one
  minor release with an attribute that makes the compiler warn.
