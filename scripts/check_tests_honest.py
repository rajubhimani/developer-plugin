"""Fail when a branch made its tests easier to pass instead of making the code pass them.

    python3 scripts/check_tests_honest.py [--base REF]

Reads the diff from REF (default: the merge base with origin/main, then main) to HEAD and looks
only at test files. It reports:

  - a skip, disable, ignore or focus marker that the diff adds
  - assertions the diff removes beyond those it adds in the same file
  - a test file the diff deletes

A line carrying `honest-ok: <reason>` is allowed, for a skip that is deliberate and explained.
This is the part a machine can see. A reviewer still looks for special-cased inputs and tests
that cannot fail (see the testing-strategy skill). Standard library only; never changes files.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]*\.py$|_test\.(go|py|cpp|c|rs)$|\.(test|spec)\.[cm]?[jt]sx?$"
    r"|(^|/)[^/]*Tests?\.(java|kt)$|(^|/)src/test/")
MARKERS = re.compile(
    r"@pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|@unittest\.(skip|expectedFailure)|self\.skipTest\("
    r"|\b(it|test|describe)\.(skip|only)\b|\b(xit|xdescribe|xtest|fit|fdescribe)\(|\bt\.Skip(Now)?\("
    r"|#\[ignore\b|@Disabled\b|@Ignore\b|GTEST_SKIP\(|\bDISABLED_")
ASSERTION = re.compile(
    r"\bassert\w*\b|\bexpect\(|\bt\.(Error|Errorf|Fatal|Fatalf)\(|\bassert_(eq|ne)!|\bREQUIRE\(|\bEXPECT_|\bASSERT_")
ALLOWED = re.compile(r"honest-ok:\s*\S+")


def git(*args: str) -> str:
    """Run git and return its output, failing with its message."""
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def default_base() -> str:
    """Return the merge base with the integration branch, or HEAD~1 when there is none."""
    for branch in ("origin/main", "main", "origin/master", "master"):
        done = subprocess.run(["git", "merge-base", branch, "HEAD"], capture_output=True, text=True, check=False)
        if done.returncode == 0 and done.stdout.strip():
            return done.stdout.strip()
    return "HEAD~1"


def findings(diff: str) -> list[str]:
    """Return the problems a unified diff shows in test files."""
    problems: list[str] = []
    path, removed, added, in_test = "", 0, 0, False

    def close() -> None:
        if in_test and removed > added:
            problems.append(f"{path}: {removed - added} assertion(s) removed (the diff removes {removed} and adds {added})")

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            close()
            path, removed, added = line.rsplit(" b/", 1)[-1], 0, 0
            in_test = bool(TEST_PATH.search(path))
        elif line.startswith("deleted file mode") and in_test:
            problems.append(f"{path}: test file deleted")
            in_test = False
        elif not in_test or line.startswith(("+++", "---")):
            continue
        elif line.startswith("+") and not line.startswith("++"):
            if MARKERS.search(line) and not ALLOWED.search(line):
                problems.append(f"{path}: adds a skip or focus marker: {line[1:].strip()[:80]}")
            added += bool(ASSERTION.search(line))
        elif line.startswith("-") and not line.startswith("--"):
            removed += bool(ASSERTION.search(line))
    close()
    return problems


def main(argv: list[str]) -> int:
    """Check the branch's test changes."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default=None, help="the ref the branch started from")
    args = parser.parse_args(argv)
    base = args.base or default_base()
    found = findings(git("diff", "--no-color", "-U0", f"{base}...HEAD" if args.base else f"{base}..HEAD"))
    for line in found:
        print(f"FAIL {line}")
    if found:
        print("Make the code pass the tests, not the tests pass. A deliberate skip needs 'honest-ok: <reason>' on its line.")
        return 1
    print(f"tests honest: no skip marker added, no assertion removed, no test file deleted since {base[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
