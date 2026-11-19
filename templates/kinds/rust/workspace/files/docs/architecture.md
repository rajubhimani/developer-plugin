# Architecture

## Layout

```text
Cargo.toml          virtual manifest (no [package]): members, shared metadata, lints
crates/<member>/    a library or a binary; all crates are siblings in one folder
Cargo.lock          the only lock file
```

Crates are named `{{scope}}-<member>` and imported as `{{package}}_<member>`.

## Rules

1. Keep the crate list flat under `crates/`; Cargo's namespace is flat too, and a flat
   list makes splitting and merging crates easy.
2. Binaries are thin: they gather input and set the exit code. Logic lives in libraries.
3. Libraries never depend on binaries. A binary depends on the libraries it needs.
4. Declare a dependency version once in `[workspace.dependencies]`; a member writes
   `name.workspace = true`. A member depends on a sibling through the workspace, not by a
   relative path of its own.
5. Share metadata (`version`, `edition`, `license`) and lints through `[workspace.package]`
   and `[workspace.lints]`; members inherit them.
6. Set the resolver explicitly (a virtual manifest has no package edition to infer it
   from). `[profile.*]` and `[patch]` sections only work in the root manifest.
7. Keep the `unsafe` count at zero; if a crate needs it, isolate it in one small crate
   with a safety comment on each block.

## Ownership

`.github/CODEOWNERS` names who reviews each folder. Shared libraries get the strictest
review.

## Members

| Member | Kind | Purpose |
|---|---|---|
{{member_rows}}
