"""The public API is a promise: test it through the package, not the private modules."""

import pytest

import {{package}}


def test_every_name_in_all_exists() -> None:
    for name in {{package}}.__all__:
        assert hasattr({{package}}, name), name


def test_version_is_a_string() -> None:
    assert isinstance({{package}}.__version__, str)


def test_greet_returns_a_greeting() -> None:
    assert {{package}}.greet("world") == "Hello, world!"


def test_greet_rejects_an_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        {{package}}.greet("  ")


def test_private_modules_are_not_part_of_the_api() -> None:
    assert not any(name.startswith("_") and name != "__version__" for name in {{package}}.__all__)
