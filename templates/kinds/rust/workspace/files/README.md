# {{title}}

<one line: what this repository holds>

```text
crates/<member>/   one crate per folder, a flat list (libraries and binaries)
Cargo.toml         virtual manifest: members, shared versions, shared lints
Cargo.lock         commit it: the workspace builds applications
```

Replace the `<edition>` and `<resolver>` placeholders in `Cargo.toml` with current
values, then `cargo test --workspace` (`make check`). Layout and rules:
[docs/architecture.md](docs/architecture.md); `make structure-check` enforces them.
