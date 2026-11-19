//! Entry point. Keep it thin: gather input, call the library, turn the result into an
//! exit code. The logic lives in `lib.rs` where tests reach it.

use std::io::{self, Write};
use std::process::ExitCode;

fn main() -> ExitCode {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    match {{package}}::run(std::env::args().skip(1), &mut out) {
        Ok(()) => ExitCode::SUCCESS,
        Err({{package}}::Error::Usage) => {
            let _ = writeln!(io::stderr(), "usage: {{name}} <name>");
            ExitCode::from(2)
        }
    }
}
