"""Command line interface: parse arguments, call plain functions, return an exit code.

Keep this module thin. Put the real work in functions that take plain values and
return plain values, so tests call them without a terminal. For many subcommands
consider Typer or Click; the structure below stays the same.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version

EXIT_OK = 0
EXIT_USAGE = 2


def program_version() -> str:
    """Return the installed version."""
    try:
        return version("{{name}}")
    except PackageNotFoundError:
        return "0+unknown"


def greet(name: str, *, shout: bool = False) -> str:
    """Return the greeting. Replace with the tool's real behaviour."""
    text = f"Hello, {name}!"
    return text.upper() if shout else text


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="{{name}}",
        description="<one line: what this command does>",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {program_version()}")
    parser.add_argument("name", help="who to greet")
    parser.add_argument("--shout", action="store_true", help="use capital letters")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command and return its exit code (0 success, 2 bad usage, 1 failure).

    Results go to standard output; messages for people go to standard error.
    """
    args = build_parser().parse_args(argv)
    try:
        print(greet(args.name, shout=args.shout))
    except Exception as exc:  # last stop for the process: report once, exit non-zero
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return EXIT_OK
