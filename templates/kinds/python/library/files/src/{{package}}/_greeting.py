"""Private implementation module. Import from the package, not from here."""


def greet(name: str) -> str:
    """Return a greeting for `name`.

    Replace this example with the library's real behaviour. Keep each public function
    typed, documented, and covered by a test in tests/test_public_api.py.

    >>> greet("world")
    'Hello, world!'
    """
    if not name.strip():
        raise ValueError("name must not be empty")
    return f"Hello, {name}!"
