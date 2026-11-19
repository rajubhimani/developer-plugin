"""Test the command through main(argv), the way the installed command runs it."""

import pytest

from {{package}}.cli import main


def test_prints_a_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["world"]) == 0
    assert capsys.readouterr().out == "Hello, world!\n"


def test_shout_option(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["world", "--shout"]) == 0
    assert capsys.readouterr().out == "HELLO, WORLD!\n"


def test_version_option_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        main(["--version"])
    assert stop.value.code == 0
    assert "{{name}}" in capsys.readouterr().out


def test_missing_argument_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        main([])
    assert stop.value.code == 2
    assert "usage" in capsys.readouterr().err.lower()
