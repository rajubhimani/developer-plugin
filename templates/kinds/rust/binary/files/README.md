# {{title}}

<one line: what this program does>

Replace the `<edition>` placeholder in `Cargo.toml`, then `cargo run -- world` and
`make check`. Commit `Cargo.lock`: this is an application.

`src/main.rs` only gathers input and sets the exit code; `src/lib.rs` holds the logic and
its tests. Exit code 0 is success, 2 is bad usage. Options and exit codes are the public
interface and follow semantic versioning.
