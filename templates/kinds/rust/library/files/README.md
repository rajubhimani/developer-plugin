# {{title}}

<one line: what this library does and who it is for>

```toml
[dependencies]
{{name}} = "<version>"
```

## Develop

Replace the `<edition>` placeholder in `Cargo.toml` with the current edition, then:
`cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`
(`make check`). A published library does not need `Cargo.lock` committed; an
application does.

## Public API and versions

Every `pub` item is public and follows semantic versioning. Return typed errors
(an enum callers can match on); do not `unwrap` in library code. Record changes in
[CHANGELOG.md](CHANGELOG.md).
