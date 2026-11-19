//! The program's logic, kept out of `main` so it can be tested without a process.

use std::fmt;
use std::io::Write;

/// Why a run failed.
#[derive(Debug, PartialEq, Eq)]
pub enum Error {
    /// The arguments were not what the program expects.
    Usage,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Usage => write!(f, "bad usage"),
        }
    }
}

impl std::error::Error for Error {}

/// Runs the program with `args` (without the program name), writing results to `out`.
/// Results go to standard output; messages for people go to standard error.
pub fn run<I, W>(args: I, out: &mut W) -> Result<(), Error>
where
    I: IntoIterator<Item = String>,
    W: Write,
{
    let args: Vec<String> = args.into_iter().collect();
    let [name] = args.as_slice() else {
        return Err(Error::Usage);
    };
    // Ignoring a failed write to a closed pipe is deliberate for a command line tool.
    let _ = writeln!(out, "Hello, {name}!");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run_with(args: &[&str]) -> (Result<(), Error>, String) {
        let mut out = Vec::new();
        let result = run(args.iter().map(|a| a.to_string()), &mut out);
        (result, String::from_utf8(out).expect("utf-8 output"))
    }

    #[test]
    fn greets() {
        assert_eq!(
            run_with(&["world"]),
            (Ok(()), "Hello, world!\n".to_string())
        );
    }

    #[test]
    fn no_arguments_is_a_usage_error() {
        assert_eq!(run_with(&[]).0, Err(Error::Usage));
    }
}
