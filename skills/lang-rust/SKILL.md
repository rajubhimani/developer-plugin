---
name: lang-rust
description: Rust project setup and quality gates (rustup toolchain, cargo workspaces, clippy, rustfmt, cargo-deny, cargo-audit). Use when creating, changing, reviewing or building Rust crates.
verified: 2026-11-07
---

# Rust

## Current versions

Look these up when you start: the stable channel manifest at
`https://static.rust-lang.org/dist/channel-rust-stable.toml`, or `rustup check`.

## Setup

- Pin the toolchain in `rust-toolchain.toml` (channel `stable` or an exact
  version) so every machine and CI run uses the same compiler.
- Use the newest edition the toolchain supports for new crates. Check the Cargo
  Book for the resolver it implies before relying on it.
- Use a workspace for more than one crate. Put shared versions in
  `[workspace.dependencies]` and shared lints in `[workspace.lints]`, and let each
  crate opt in.
- Commit `Cargo.lock` for binaries. For libraries, follow the team's policy.

## Quality gates

1. `cargo fmt --all -- --check`
2. `cargo clippy --all-targets --all-features -- -D warnings`
3. `cargo test --workspace --all-features`
4. `cargo deny check` (licences, banned crates, duplicate versions, sources)
   with a `deny.toml` file.
5. `cargo audit` against the RustSec advisory database, or rely on `cargo deny`
   advisories if it covers your needs.
6. If the crate declares a minimum supported Rust version, test it in CI.

## Common mistakes

- `unwrap()` and `expect()` in library code paths that can fail for normal input.
- Ignoring clippy warnings with blanket `allow` attributes instead of fixing them.
- Unpinned git dependencies in release builds.

Source to check before relying on details: The Cargo Book, the Clippy and
rustfmt documentation, and the cargo-deny docs.
