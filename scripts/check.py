"""Run the plugin's checks without make, so Windows can run them too.

Usage: python3 scripts/check.py   (the same checks as `make check`)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    [sys.executable, "scripts/validate.py"],
    [sys.executable, "scripts/sync_rules.py", "--check"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
]


def main() -> int:
    """Run each check in order and stop at the first failure."""
    for step in STEPS:
        print("+", " ".join(step[1:]), flush=True)
        result = subprocess.run(step, cwd=ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
