//! {{title}}: <one line: what this library does>.
//!
//! The public API is every `pub` item reachable from this file. Keep the surface small,
//! document each item with an example (doc tests run as tests), and change it only as
//! semantic versioning allows.

use std::fmt;

/// Errors returned by this crate. Callers can match on the variants.
#[derive(Debug, PartialEq, Eq)]
pub enum Error {
    /// The name was empty or only whitespace.
    EmptyName,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::EmptyName => write!(f, "name must not be empty"),
        }
    }
}

impl std::error::Error for Error {}

/// Returns a greeting for `name`. Replace with the library's real behaviour.
///
/// ```
/// assert_eq!({{package}}::greet("world").unwrap(), "Hello, world!");
/// ```
pub fn greet(name: &str) -> Result<String, Error> {
    if name.trim().is_empty() {
        return Err(Error::EmptyName);
    }
    Ok(format!("Hello, {name}!"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn greets() {
        assert_eq!(greet("world"), Ok("Hello, world!".to_string()));
    }

    #[test]
    fn rejects_a_blank_name() {
        assert_eq!(greet("  "), Err(Error::EmptyName));
    }
}
